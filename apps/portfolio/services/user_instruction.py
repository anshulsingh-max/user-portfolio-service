"""
    User instruction service
"""
import json
import logging
import uuid

import requests
from django.conf import settings
from datetime import datetime

from apps.exceptions.user_instructions import OrderAlreadyExecuted
from apps.portfolio.constants import OrderStatus, RebalanceTransactionStates, BUSINESS_REBALANCE_CALLBACK_URL, \
    FailureMessage, RebalanceTypes, Proxy, PhaseCallbackLogEnum
from apps.exceptions.user_portfolio import UserInstructionNotFound
from apps.portfolio.models import PortfolioRebalanceTransaction, UserInstruction, UserPortfolioRebalance, \
    OrderInstruction
from apps.portfolio.models.phase_callback_log import PhaseCallbackLog
from apps.portfolio.serializers.order_instructions import OrderInstructionSerializer
from apps.portfolio.serializers.user_instruction import UserInstructionSerializer
from multitenant.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


def create_user_instruction(user_portfolio_rebalance_transaction_id):
    """
        Iterates through the stocks mentioned in the user_portfolio_rebalance and create their instructions
        'uprt' abbreviation refers to user_portfolio_rebalance_transactions
        :param user_portfolio_rebalance_transaction_id:
        :return:
    """
    logger.info(f"In create_user_instruction {user_portfolio_rebalance_transaction_id = }")
    uprt_obj = PortfolioRebalanceTransaction.objects.get(id=user_portfolio_rebalance_transaction_id)
    user_instruction_created = False
    for stock_details in uprt_obj.allocation_quantity:
        user_instruction_data = stock_details
        user_instruction_data['portfolio_rebalance_transaction'] = uprt_obj.id
        user_instruction_data['order_tag'] = f"{uuid.uuid4()}"
        logger.info(f"{user_instruction_data = }")
        ser = UserInstructionSerializer(data=user_instruction_data)
        if ser.is_valid(raise_exception=True):
            ser.save()
            user_instruction_created = True
    if not user_instruction_created:
        logger.info(f"PortfolioRebalanceTransaction as completed for {user_portfolio_rebalance_transaction_id =}")
        uprt_obj.current_state = RebalanceTransactionStates.COMPLETED.value
        uprt_obj.save()


def update_trade_details(trade_details):
    """
    Updates the trade details
    :param trade_details:
    :return:
    """
    logger.info(f"In update_trade_details {trade_details = }")
    user_inst_obj = UserInstruction.objects.get(order_tag=trade_details['order_tag'])

    if trade_already_filled(user_inst_obj):
        raise OrderAlreadyExecuted(message=f"Order tag: {trade_details['order_tag']}")

    reason = FailureMessage.DEFAULT.value if (trade_details["status"] in OrderStatus.FAILURE_STATES.value and
                                              not trade_details.get("reason")) else trade_details.get("reason")
    user_inst_obj.trade_placement_id = trade_details["trade_placement_id"]
    user_inst_obj.value = trade_details["value"]
    user_inst_obj.status = trade_details["status"]
    user_inst_obj.filled_quantity = trade_details['quantity']
    user_inst_obj.reason = reason
    user_inst_obj.retry_allowed = trade_details["retry_allowed"]
    user_inst_obj.price = trade_details.get('price')
    user_inst_obj.save()
    logger.info(
        f"Saved User Instructions from callback {UserInstructionSerializer(instance=user_inst_obj).data}, "
        f"{user_inst_obj.retry_allowed = } ")


def trade_already_filled(user_inst_obj):
    """
    Checks whether order is executed or not
    :param user_inst_obj: user instruction object
    :return:
    """
    if user_inst_obj.status == OrderStatus.FILLED.value:
        return True
    return False


def expected_rebalance_transaction_status(portfolio_rebalance_transaction):
    """
    It will check if all the user instructions are executed
    :param portfolio_rebalance_transaction:
    :return:
    """
    logger.info(f"In expected_rebalance_transaction_status {portfolio_rebalance_transaction = }")
    user_inst_queryset = UserInstruction.objects.filter(portfolio_rebalance_transaction=portfolio_rebalance_transaction)
    filled_count = 0
    for user_inst in user_inst_queryset:
        if user_inst.status in OrderStatus.WAITING_STATES.value:
            return RebalanceTransactionStates.PROCESSING.value
        if user_inst.status in OrderStatus.FILLED.value:
            filled_count += 1

    if filled_count == len(user_inst_queryset):
        return RebalanceTransactionStates.COMPLETED.value

    return RebalanceTransactionStates.PARTIALLY_COMPLETED.value


def get_user_rebalancing_instruction(id):
    try:
        logger.info(f"in get user rebalancing instruction service {id = }")
        user_instruction_query_set = UserInstruction.objects.get(id=id)
        return user_instruction_query_set
    except UserInstruction.DoesNotExist as exc:
        logger.info("User Instruction does not exist")
        logger.exception(exc)
        raise UserInstructionNotFound(message=f"user instruction not found for '{id =}'. ") from exc
    except Exception as exc:
        logger.info(f"Error in get User instruction by ID")
        logger.exception(exc)
        raise exc


def business_rebalance_sell_callback(user_portfolio_rebalance_id, rebalance_transaction_id):
    """
    This function triggers a callback which will send the details of executed (sell) and upcoming (buy) phase to
    rebalance business service so that it can start the buying of stocks
    :param user_portfolio_rebalance_id:
    :param rebalance_transaction_id:
    :return: None
    """
    phase = f"{rebalance_transaction_id}_buy_ready"
    logger.info(f"In business_rebalance_sell_callback {user_portfolio_rebalance_id = }, {phase = }")
    uprt_obj = UserPortfolioRebalance.objects.get(id=user_portfolio_rebalance_id)
    logger.info(
        f"Fetched UserPortfolioRebalance object: id={uprt_obj.id}, is_sell_completed={uprt_obj.is_sell_completed}, "
        f"type={uprt_obj.type}, proxy={uprt_obj.proxy}")
    if uprt_obj.is_sell_completed and uprt_obj.type != RebalanceTypes.RECONCILIATION.value and uprt_obj.proxy == Proxy.USER.value:
        if not PhaseCallbackLog.objects.filter(phase_id=phase).exists():
            logger.info("Sell phase completed and rebalance is eligible for business callback.")
            phase_callback_obj = PhaseCallbackLog.objects.create(
                user_id=UserPortfolioRebalance.objects.get(id=user_portfolio_rebalance_id).user_portfolio.user_id,
                portfolio_rebalance_transaction_id=rebalance_transaction_id,
                phase_id=phase
            )
            phase_details = uprt_obj.get_phase_details_of_rebalance

            logger.info(f"Phase details prepared for callback: {phase_details}")
            metadata = phase_details.get("metadata")
            tenant_id = metadata.get("tenant_id")
            headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenant_id,
                'X-API-KEY': settings.REBALANCE_BUSINESS_SERVICE_API_KEY
            }
            logger.info(f"Sending POST request to {BUSINESS_REBALANCE_CALLBACK_URL} with headers: {headers}")
            callback_response = requests.post(BUSINESS_REBALANCE_CALLBACK_URL, data=json.dumps(phase_details),
                                              headers=headers)
            logger.info(f"{callback_response.text = }")

            phase_callback_obj.status = PhaseCallbackLogEnum.COMPLETED.value
            phase_callback_obj.save()
            logger.info(f"Callback successfully completed for {user_portfolio_rebalance_id = }")
            callback_response.raise_for_status()
        else:
            logger.info(f"Callback already registered for {user_portfolio_rebalance_id = } and {phase = }")


def user_portfolio_business_event_callback(event_details):
    logger.info(f"In user_portfolio_business_event_callback {event_details = }")
    callback_response = requests.post(f"{settings.USER_PORTFOLIO_BUSINESS_URL}/user-portfolio/event",
                                      data=json.dumps(event_details),
                                      headers={
                                          'Content-Type': 'application/json',
                                          'X-Tenant-ID': get_current_tenant()
                                      })
    logger.info(f"user_portfolio_business_event_callback {callback_response.json() =}")
    if callback_response.status_code != 200:
        return callback_response.json(), False
    return True, True


def update_order_instructions(trade_details):
    """
    Updates the order instructions based on provided trade details.

    This function retrieves an `OrderInstruction` object using the `order_tag` from `trade_details`,
    checks if the order has already been executed, and updates the relevant fields.

    Args:
        trade_details (dict): A dictionary containing the trade details with the following keys:
            - order_tag (str): The unique identifier for the order.
            - trade_placement_id (int): The ID of the trade placement.
            - value (float): The value of the order (can be None).
            - status (str): The status of the order.
            - quantity (float): The filled quantity of the order.
            - reason (str, optional): The reason for the order status, if available.

    Raises:
        - OrderAlreadyExecuted: If the order has already been executed.

    Logs:
        - Logs the input trade details.
        - Logs the serialized user instruction after saving.

    Example:
        trade_details = {
            "order_tag": "ORDER_001",
            "trade_placement_id": 123,
            "value": 15000.0,
            "status": "completed",
            "quantity": 100.0,
            "reason": "Order partially filled"
        }
        update_order_instructions(trade_details)
    """

    logger.info(f"In update_order_instructions with trade_details: {trade_details}")

    try:
        order_inst_obj = OrderInstruction.objects.get(order_tag=trade_details['order_tag'],
                                                      status=OrderStatus.WAITING.value)
    except OrderInstruction.DoesNotExist:
        logger.error(f"OrderInstruction with order_tag {trade_details['order_tag']} does not exist.")
        raise

    if trade_already_filled(order_inst_obj):
        raise OrderAlreadyExecuted(message=f"Order tag: {trade_details['order_tag']}")

    reason = (FailureMessage.DEFAULT.value
              if trade_details["status"] in OrderStatus.FAILURE_STATES.value
                 and not trade_details.get("reason")
              else trade_details.get("reason"))

    order_inst_obj.trade_placement_id = trade_details["trade_placement_id"]
    order_inst_obj.value = trade_details.get("value")
    order_inst_obj.status = trade_details["status"]
    order_inst_obj.filled_quantity = trade_details['quantity']
    order_inst_obj.order_price = trade_details['price']
    order_inst_obj.reason = reason

    order_inst_obj.save()

    logger.info(f"Updated User Instructions: {OrderInstructionSerializer(instance=order_inst_obj).data}")
