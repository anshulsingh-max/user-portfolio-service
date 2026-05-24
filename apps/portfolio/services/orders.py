"""
This module contains service functions related to order management in the portfolio system.

It includes utility functions to handle the state transitions and logic required for processing
and managing orders and order instructions. These functions assist in evaluating the conditions
that influence the state of an order and provide the appropriate next state based on predefined
business rules.

Classes/Enums imported:
    - Side: Enum representing the order side (buy/sell).
    - OrderStates: Enum representing the possible states of an order.
    - OrderStatus: Enum representing the current status of an order (e.g., filled, pending).

Functions:
    - get_next_order_state(instance): Determines the next state of an order based on the
      current status, side, and stop loss settings of the order instruction.
"""
import logging

from django.db.models import Q
from django.db import transaction

from apps.portfolio.constants import Side, OrderCurrentStatus, OrderStatus, OrderInstructionSources
from apps.portfolio.models import OrderInstruction, Basket, Order

logger = logging.getLogger(__name__)


def get_next_order_state(instance):
    """
    Determine the next state of an order based on the current instance details.

    This function checks the stop loss, side (buy/sell), and the current status of the order to decide whether
    the order state should transition to the 'MONITORING' state. If the conditions are not met, the current state
    of the order is returned.

    Args:
        instance (OrderInstruction): The instance of the `OrderInstruction` that is being evaluated.

    Returns:
        str: The next state of the order. If the conditions are met, returns `OrderStates.MONITORING.value`;
        otherwise, returns the current state of the associated order.

    Logic:
        - If the stop loss is not set, the side is 'BUY', and the order status is 'FILLED', the state transitions
          to 'MONITORING'.
        - Otherwise, the function returns the current state of the associated order.
    """
    logger.info(f"In get_next_order_state {instance}")
    side = instance.side
    status = instance.status

    if side == Side.SELL.value and (instance.order.sell_quantity != instance.order.buy_quantity):
        logger.info(f"Sell order quantity does not match buy order quantity {instance.order.id}")
        return OrderCurrentStatus.BUY.value

    state_map = {
        (Side.BUY.value, OrderStatus.FILLED.value): OrderCurrentStatus.BUY.value,
        (Side.BUY.value, OrderStatus.WAITING.value): OrderCurrentStatus.BUY_IN_PROGRESS.value,
        (Side.BUY.value, OrderStatus.CANCEL.value): OrderCurrentStatus.BUY_IN_PROGRESS.value,
        (Side.SELL.value, OrderStatus.FILLED.value): OrderCurrentStatus.SELL.value,
        (Side.SELL.value, OrderStatus.WAITING.value): OrderCurrentStatus.SELL_IN_PROGRESS.value,
    }

    return state_map.get((side, status), instance.order.current_status)


def skip_orders(basket_id, new_status):
    """
    Marks the status of all orders to skip within a specific basket where the current status
    is either 'BUY_IN_PROGRESS'.

    Args:
        basket_id (int): The ID of the basket whose orders need to be updated.
        new_status (str): The new status to be applied to the orders that are in 'BUY_IN_PROGRESS' or 'SELL_IN_PROGRESS'.

    Process:
        1. Fetches all orders associated with the provided basket that are either in
           the 'BUY_IN_PROGRESS' or 'SELL_IN_PROGRESS' status.
        2. Updates the `current_status` of each fetched order to the new status provided.
        3. Saves the updated status of each order to the database.

    Logging:
        Logs the basket ID and the new status being applied for debugging purposes.

    Example Usage:
        basket_id = 123
        new_status = 'COMPLETED'
        update_order_status_for_basket(basket_id, new_status)
    """
    logger.info(f"In skip_orders {basket_id =}, {new_status =}")

    filtered_orders = Order.objects.filter(
        current_status=OrderCurrentStatus.BUY_IN_PROGRESS.value,
        basket=basket_id
    )
    logger.info(f"Filtered orders: {filtered_orders}")
    with transaction.atomic():
        logger.info(f"Updating {len(filtered_orders)} orders to {new_status}")
        for order in filtered_orders:
            logger.info(f"Updating order {order.id} to {new_status}")
            order.current_status = new_status
            order.save()

            updated_count = OrderInstruction.objects.filter(order=order).update(
                source=OrderInstructionSources.SKIP.value
            )
            logger.info(
                f"Order {order.id} skipped. Updated {updated_count} related instructions to SKIP."
            )
    logger.info(f"Orders skipped for basket {basket_id}")