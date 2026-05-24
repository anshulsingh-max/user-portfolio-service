"""
    Services module for User Portfolio Rebalance
"""
import logging

from bw_essentials.notifications.teams_notifications import Notifications

from apps.exceptions.user_portfolio_rebalance_exceptions import PortfolioRebalancePending
from apps.portfolio.constants import (RebalanceTransactionStates, RebalanceTransactionTypes, States, Side,
                                      Strategy, RebalanceCloseReason, RebalanceTypes, CashTransaction)
from apps.portfolio.models import UserPortfolioRebalance, UserInstruction, PortfolioRebalanceTransaction
from apps.portfolio.serializers.user_instruction import ReadUserInstructionSerializer
from apps.portfolio.services.user_instruction import user_portfolio_business_event_callback
from apps.portfolio.services.user_portfolio import get_event_details
from apps.portfolio.tasks.send_notification_event import send_investment_succeeded_event,send_withdrawal_succeeded_event
from multitenant.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


def get_next_state(instance, rebalance_transaction_state, rebalance_transaction_type):
    """
    Gets the next state of user portfolio rebalance
    :param rebalance_transaction_type:
    :param rebalance_transaction_state:
    :param instance:
    :return:
    """
    logger.info(f"In get next state {instance = }, {rebalance_transaction_state = }, "
                f"{rebalance_transaction_type = }")
    if rebalance_transaction_state == RebalanceTransactionStates.SKIPPED.value:
        if rebalance_transaction_type == RebalanceTransactionTypes.INITIAL.value:
            return States.COMPLETE.value
        if rebalance_transaction_type == RebalanceTransactionTypes.T0.value:
            return States.COMPLETE.value

    if rebalance_transaction_state in [RebalanceTransactionStates.COMPLETED.value,
                                       RebalanceTransactionStates.MANUALLY_COMPLETED.value]:
        if rebalance_transaction_type == RebalanceTransactionTypes.INITIAL.value:
            return States.COMPLETE.value
        if rebalance_transaction_type == RebalanceTransactionTypes.T0.value:
            max_rebalance_ratio = instance.user_inputs.get('max_rebalance_ratio')
            if (not max_rebalance_ratio) or (max_rebalance_ratio<1):
                return States.PARTIAL.value
            else:
                return States.COMPLETE.value
        if rebalance_transaction_type == RebalanceTransactionTypes.T1.value:
            return States.COMPLETE.value
        if rebalance_transaction_type == RebalanceTransactionTypes.CASH_ALLOCATION.value:
            return States.COMPLETE.value

    return instance.current_state


def update_rebalance_state(instance, rebalance_transaction_state, rebalance_transaction_type):
    """
    Update rebalance transaction state
    :param rebalance_transaction_type:
    :param rebalance_transaction_state:
    :param instance:
    :return:
    """
    logger.info(f"In update_rebalance_state {instance = }, {rebalance_transaction_state = }, "
                f"{rebalance_transaction_type = }")
    state = get_next_state(instance, rebalance_transaction_state, rebalance_transaction_type)
    previous_state = instance.current_state
    instance.current_state = state
    instance.save()
    # as this is a signal we put other actions in try except to avoid breaking the flow in case of
    # any failure in other actions. The main flow is to update the state and save the instance,
    # which is already done before
    try:
        tenant_id = get_current_tenant()
        # Fire "Investment Succeeded" for INITIAL rebalances (add) that complete
        if (state == States.COMPLETE.value
                and previous_state != States.COMPLETE.value
                and instance.type == RebalanceTypes.INITIAL.value
                and instance.transaction_type == CashTransaction.ADD.value):

            logger.info(f"Triggering investment succeeded event for rebalance {instance.id}")
            send_investment_succeeded_event.delay(instance.id, tenant_id=tenant_id)
        if (state == States.COMPLETE.value
                and previous_state != States.COMPLETE.value
                and instance.type == RebalanceTypes.INITIAL.value
                and instance.transaction_type == CashTransaction.WITHDRAW.value):
            logger.info(f"Triggering withdrawal succeeded event for rebalance {instance.id}")
            send_withdrawal_succeeded_event.delay(instance.id, tenant_id=tenant_id)
    except Exception as exc:
        notifier=Notifications('User Portfolio Service')
        notifier.notify_error(f"Error in post state update actions for rebalance {instance.id}: {exc}",)
        logger.exception(f"Error in post state update actions for rebalance {instance.id}: {exc}")




def is_rebalance_active(user_portfolio_id, raise_exception=False):
    """
    Checks if the rebalance is active or not for the user portfolio
    :param user_portfolio_id:
    :param raise_exception: In case of true raises the exception else will return True or False
    :return:
    """
    logger.info(f"In is_rebalance_active {user_portfolio_id = }, {raise_exception = }")
    bool_response = UserPortfolioRebalance.objects.filter(user_portfolio=user_portfolio_id).exclude(
        current_state=States.COMPLETE.value).exists()
    if bool_response and raise_exception:
        logger.info(f"In exception {bool_response = }, {raise_exception = }")
        raise PortfolioRebalancePending(message=f"User portfolio id {user_portfolio_id}")
    return bool_response


def get_portfolio_rebalance(user_portfolio_id, current_state):
    """
    Will get the user portfolio rebalances according to the current state and user portfolio id
    :param user_portfolio_id:
    :param current_state:
    :return:
    """
    portfolio_rebalance_queryset = (UserPortfolioRebalance.objects.filter(user_portfolio=user_portfolio_id,
                                                                         current_state__in=current_state)
                                    .order_by("-id").prefetch_related('portfolio_rebalance_transactions',
                                                                      'portfolio_rebalance_transactions__user_instructions'))
    return portfolio_rebalance_queryset


def manually_complete_latest_transaction(user_portfolio_id: int) -> PortfolioRebalanceTransaction | None:
    """Mark the most recent eligible transaction for a portfolio as manually completed."""
    logger.info(f"Manually completing latest transaction for user_portfolio_id={user_portfolio_id}")

    latest_rebalance = (
        UserPortfolioRebalance.objects
        .filter(
            user_portfolio_id=user_portfolio_id,
            current_state__in=[States.PARTIAL.value, States.PENDING.value],
        )
        .order_by("-created")
        .first()
    )
    if not latest_rebalance:
        logger.info(
            "No partial or pending rebalance found for manual completion",
            extra={"user_portfolio_id": user_portfolio_id},
        )
        return None

    latest_transaction = (
        PortfolioRebalanceTransaction.objects
        .filter(
            portfolio_rebalance=latest_rebalance,
            current_state=RebalanceTransactionStates.PARTIALLY_COMPLETED.value,
        )
        .select_related("portfolio_rebalance")
        .order_by("-created")
        .first()
    )
    if not latest_transaction:
        logger.info(
            "No eligible transaction found for manual completion",
            extra={
                "user_portfolio_id": user_portfolio_id,
                "user_portfolio_rebalance_id": latest_rebalance.id,
            },
        )
        return None

    latest_transaction.current_state = RebalanceTransactionStates.MANUALLY_COMPLETED.value
    latest_transaction.save(update_fields=["current_state", "modified"])

    logger.info(f"Marked transaction as manually completed for user_portfolio_id={user_portfolio_id}, "
                f"transaction_id={latest_transaction.id}")
    return latest_transaction


def get_latest_user_instructions_of_rebalance(user_portfolio_rebalance_id, rebalance_transaction_types):
    """
    A function to get the orders/user instructions of a rebalance according to it's type
    It only gets latest of each symbol eg. SBIN was failed in 1st attempt but executed in later attempt, then only the
    latest executed one will be bought
    :param user_portfolio_rebalance_id:  Rebalance id of user portfolio
    :param rebalance_transaction_types: Rebalance transaction type like initial,t0,t1 (list)
    :return:
    """
    logger.info(f"{user_portfolio_rebalance_id = }, {rebalance_transaction_types = }")
    user_instruction_list = UserInstruction.objects.filter(
        portfolio_rebalance_transaction__type__in=rebalance_transaction_types,
        portfolio_rebalance_transaction__portfolio_rebalance=user_portfolio_rebalance_id).order_by('id')

    all_orders = ReadUserInstructionSerializer(instance=user_instruction_list, many=True).data
    orders_dict = {}
    for order in all_orders:
        orders_dict[order['symbol']] = order

    logger.info(f"{orders_dict = }")
    orders_dict = sorted(orders_dict.items())
    return [order[1] for order in orders_dict]


def get_user_instructions(upr_id, side, status, excluded_states=[]):
    """
    A function to get the orders/user instructions of a rebalance according to it's type
    :param upr_id:  Rebalance id of user portfolio
    :param side: Side of order
    :param status: Status of order
    :return:
    """
    logger.info(f"In get_user_instructions {upr_id = }, {side = }, {status}")
    user_instruction_queryset = UserInstruction.objects.filter(
        portfolio_rebalance_transaction__portfolio_rebalance=upr_id,
        side=side,
        status=status).exclude(portfolio_rebalance_transaction__current_state__in=excluded_states)
    user_instruction_list = ReadUserInstructionSerializer(instance=user_instruction_queryset, many=True).data
    logger.info(f"{user_instruction_list = }")
    return user_instruction_list


def update_user_portfolio_rebalance(upr_id, data):
    """
    Updates the data in user portfolio rebalance
    :param upr_id: user portfolio rebalance id
    :param data: data to update
    :return:
    """
    logger.info("In update_user_portfolio_rebalance")
    instruction_url = data.get('instruction_url', None)
    logger.info(f"Updating instruction_url for upr_id={upr_id} -> {instruction_url}")
    UserPortfolioRebalance.objects.filter(id=upr_id).update(instruction_url=instruction_url)

    instance = PortfolioRebalanceTransaction.objects.filter(portfolio_rebalance=upr_id).order_by('-created').first()
    if instance:
        PortfolioRebalanceTransaction.objects.filter(id=instance.id).update(instruction_url=instruction_url)
        logger.info(f"Updated PortfolioRebalanceTransaction(id={instance.id}) instruction_url")
    else:
        logger.info(f"No related PortfolioRebalanceTransaction found for upr_id={upr_id}")


def close_rebalance(rebalance_id):
    """
    Manually close an ongoing rebalance.

    Steps:
    1. Only allow for portfolios with strategy=rebalance.
    2. Pick the latest rebalance matching rebalance_id.
    3. If latest transaction not complete/manually_complete/ skipped, mark manually_completed.
    4. Mark rebalance complete if not already.
    5. Compute cash_carry_forward = (cash_ingested + total_sell_value) - total_buy_value and persist reason.
    """
    logger.info("In close_rebalance service", extra={"rebalance_id": rebalance_id})
    upr = (UserPortfolioRebalance.objects.filter(id=rebalance_id).select_related("user_portfolio").
           prefetch_related("portfolio_rebalance_transactions__user_instructions").order_by("-id").first())

    if not upr:
        logger.info("No UserPortfolioRebalance found for rebalance_id", extra={"rebalance_id": rebalance_id})
        raise ValueError("UserPortfolioRebalance not found for the provided rebalance_id")

    if upr.user_portfolio.strategy != Strategy.REBALANCE.value:
        logger.info(f"Rebalance close skipped due to non-rebalance strategy: {upr.user_portfolio.strategy}, "
                    f"rebalance_id: {rebalance_id}")
        raise ValueError("User portfolio strategy must be rebalance to close the rebalance")

    latest_txn = PortfolioRebalanceTransaction.objects.filter(portfolio_rebalance=upr).order_by("-created").first()

    if latest_txn and latest_txn.current_state not in [
        RebalanceTransactionStates.COMPLETED.value,
        RebalanceTransactionStates.MANUALLY_COMPLETED.value,
    ]:
        latest_txn.current_state = RebalanceTransactionStates.MANUALLY_COMPLETED.value
        latest_txn.save()
        logger.info("Marked latest transaction manually completed", extra={"txn_id": latest_txn.id})

    if upr.current_state != States.COMPLETE.value:
        upr.current_state = States.COMPLETE.value

    cash_ingested = upr.cash_ingested or 0
    user_instructions = UserInstruction.objects.filter(portfolio_rebalance_transaction__portfolio_rebalance=upr)
    total_sell = sum((ui.value or 0) for ui in user_instructions if ui.side == Side.SELL.value)
    total_buy = sum((ui.value or 0) for ui in user_instructions if ui.side == Side.BUY.value)

    upr.cash_carry_forward = cash_ingested + total_sell - total_buy
    upr.reason = RebalanceCloseReason.MANUAL_NEW_REBALANCE.value
    upr.save()

    return {
        "user_portfolio_rebalance_id": upr.id,
        "portfolio_rebalance_transaction_id": latest_txn.id if latest_txn else None,
        "cash_carry_forward": upr.cash_carry_forward,
    }
