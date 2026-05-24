"""
    Services module for User Portfolio Rebalance Transaction
"""
import logging
import time
from django.db.models import Sum

from apps.exceptions.rebalance_transaction_exceptions import RebalanceTransactionPending
from apps.exceptions.user_portfolio_rebalance_exceptions import PortfolioRebalanceEndOfState
from apps.portfolio.constants import RebalanceTypes, States, RebalanceTransactionTypes, RebalanceTransactionStates, \
    OrderStatus
from apps.portfolio.models import UserPortfolioRebalance, PortfolioRebalanceTransaction
from apps.portfolio.services.user_instruction import expected_rebalance_transaction_status
from apps.utils.cache_lock import acquire_lock, release_lock, acquire_lock_retry

logger = logging.getLogger(__name__)


def get_type_of_rebalance_transaction(user_portfolio_rebalance_id):
    """
    This module gets the type of rebalance transaction by considering type and state of user portfolio rebalance
    'upr' is abbreviation user portfolio rebalance
    :param user_portfolio_rebalance_id: ID of user portfolio rebalance
    :return: type of rebalance transaction
    """
    logger.info(f"In get_type_of_rebalance_transaction {user_portfolio_rebalance_id = }")
    upr_obj = UserPortfolioRebalance.objects.get(id=user_portfolio_rebalance_id)
    if upr_obj.type in [RebalanceTypes.INITIAL.value, RebalanceTypes.RECONCILIATION.value] and upr_obj.current_state == States.PENDING.value:
        return RebalanceTransactionTypes.INITIAL.value
    elif upr_obj.type == RebalanceTypes.REBALANCE.value and upr_obj.current_state == States.PENDING.value:
        return RebalanceTransactionTypes.T0.value
    elif upr_obj.type == RebalanceTypes.REBALANCE.value and upr_obj.current_state == States.PARTIAL.value:
        return RebalanceTransactionTypes.T1.value
    elif upr_obj.type == RebalanceTypes.CASH_ALLOCATION.value and upr_obj.current_state == States.PENDING.value:
        return RebalanceTransactionTypes.CASH_ALLOCATION.value

    raise PortfolioRebalanceEndOfState()


def update_rebalance_transaction_state(instance, state):
    """
    Update rebalance transaction state
    :param state:
    :param instance:
    :return:
    """
    logger.info(f"In update_rebalance_transaction_state {instance = }, {state = }")
    instance.current_state = state
    instance.save()
    return instance


def is_rebalance_transaction_active(user_portfolio_rebalance_id, raise_exception=False):
    """
    Checks if the rebalance is active or not for the user portfolio
    :param user_portfolio_rebalance_id:
    :param raise_exception: In case of true raises the exception else will return True or False
    :return:
    """
    logger.info(f"In is_rebalance_transaction_active {user_portfolio_rebalance_id = }, {raise_exception = }")
    bool_response = PortfolioRebalanceTransaction.objects.filter(
        portfolio_rebalance=user_portfolio_rebalance_id,
        current_state=RebalanceTransactionStates.PROCESSING.value).exists()
    if bool_response and raise_exception:
        raise RebalanceTransactionPending(message=f"User portfolio rebalance id {user_portfolio_rebalance_id}")
    return bool_response


def update_on_user_instruction_save(portfolio_rebalance_transaction, executed_symbol, amount):
    """
    Runs all the updation tasks for the rebalance transaction which are instruction dependent
    :param portfolio_rebalance_transaction: instance obj
    :param executed_symbol: Symbol
    :param amount: Value of stock
    :return:
    """
    logger.info(f"In update_on_user_instruction_save {portfolio_rebalance_transaction = }, "
                f"{executed_symbol = }, {amount = }")
    if not portfolio_rebalance_transaction.executed_list:
        portfolio_rebalance_transaction.executed_list = [executed_symbol]
    else:
        portfolio_rebalance_transaction.executed_list += [executed_symbol]

    portfolio_rebalance_transaction.amount += amount
    portfolio_rebalance_transaction.save()


def refresh_portfolio_rebalance_transaction(portfolio_rebalance_transaction):
    """
    Refreshes the rebalance transaction status and returns all symbols from
    related user instructions as a list.
    first 5 attempts wait 1s, next 5 attempts wait 5s
    :param portfolio_rebalance_transaction: instance obj
    :return: list[str] symbols from related user instructions
    """
    logger.info(f"In refresh_portfolio_rebalance_transaction {portfolio_rebalance_transaction = }")

    lock_key = f"refresh_prt_lock:{portfolio_rebalance_transaction.id}"

    if not acquire_lock_retry(lock_key):
        raise Exception(f"Could not acquire lock {lock_key} to refresh PRT {portfolio_rebalance_transaction.id}")

    try:
        # Get all symbols from related user instructions as a list
        symbols_list = get_user_instruction_symbols_list(portfolio_rebalance_transaction)
        logger.info(f"Collected user instruction symbols: {symbols_list}")

        # Get total amount from related user instructions (sum of values)
        total_amount = get_user_instruction_total_value(portfolio_rebalance_transaction)
        logger.info(f"Total user instruction amount: {total_amount}")

        current_state = expected_rebalance_transaction_status(portfolio_rebalance_transaction)
        logger.info(f"Expected state for PortfolioRebalanceTransaction "
                    f"{portfolio_rebalance_transaction.id} -> {current_state}")

        portfolio_rebalance_transaction.current_state = current_state
        portfolio_rebalance_transaction.executed_list = symbols_list
        portfolio_rebalance_transaction.amount = total_amount
        portfolio_rebalance_transaction.save()
    finally:
        release_lock(lock_key)


def get_user_portfolio_rebalance_transaction(user_portfolio_rebalance_transaction_id):
    """
    Gets the user portfolio transaction object
    :param user_portfolio_rebalance_transaction_id: pk
    :return:
    """
    return PortfolioRebalanceTransaction.objects.get(id=user_portfolio_rebalance_transaction_id)


def get_user_instruction_symbols_list(portfolio_rebalance_transaction):
    """
    Returns all symbols from user instructions related to the given
    PortfolioRebalanceTransaction as a flat list.
    :param portfolio_rebalance_transaction: instance of PortfolioRebalanceTransaction
    :return: list[str]
    """
    logger.info(f"In get_user_instruction_symbols_list {portfolio_rebalance_transaction = }")
    return list(portfolio_rebalance_transaction.user_instructions.filter(status=OrderStatus.FILLED.value
                                                                         ).values_list("symbol", flat=True))


def get_user_instruction_total_value(portfolio_rebalance_transaction):
    """
    Returns the total amount by summing the 'value' field of all related
    user instructions for the given PortfolioRebalanceTransaction.
    :param portfolio_rebalance_transaction: instance of PortfolioRebalanceTransaction
    :return: float
    """
    logger.info(f"In get_user_instruction_total_value {portfolio_rebalance_transaction = }")
    agg = portfolio_rebalance_transaction.user_instructions.filter(status=OrderStatus.FILLED.value
                                                                   ).aggregate(total=Sum("value"))
    return float(agg.get("total") or 0)



def extract_invested_value(rebalance_transaction) -> float:
    """
    Extract the invested value from a transaction by summing user instructions.
    Buys add to the value, sells subtract.

    :param transaction: Transaction dictionary containing rebalance instructions.
    :return: Net invested value as float.
    """
    total_value = 0.0
    for instruction in rebalance_transaction.user_instructions.all():
        value = instruction.value if instruction.value else 0.0
        side = instruction.side
        total_value += value if side == "buy" else -value

    logger.debug("Extracted invested value from transaction: %.2f", total_value)
    return total_value