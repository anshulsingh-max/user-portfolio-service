"""
basket.py

This module defines service functions related to the Basket model. It provides 
business logic for creating and managing baskets within the portfolio management 
system. This module acts as an intermediary between the serializers and the 
database, encapsulating the logic for handling basket-related operations.
"""

import logging

from apps.exceptions.basket import BasketNotFound
from apps.portfolio.constants import BasketStates, OrderCurrentStatus
from apps.portfolio.models import Basket, Order
from apps.portfolio.serializers.basket import BasketSerializer

logger = logging.getLogger(__name__)


def create_basket(basket_data):
    """
    Create a new basket based on the provided data.

    This function validates the input data using the BasketSerializer, 
    creates a new Basket instance, and saves it to the database.

    Args:
        basket_data (dict): The data used to create the new basket.

    Returns:
        Basket: The newly created Basket instance.

    Raises:
        ValidationError: If the provided data is invalid.
    """
    logger.info(f"Creating basket data: {basket_data=}")
    ser = BasketSerializer(data=basket_data)
    if ser.is_valid(raise_exception=True):
        instance = ser.save()
        return instance


def get_basket_details(user_id, current_state):
    """
    Retrieve basket details for a specific user based on the current state.

    This function queries the Basket model to find baskets that match the given
    user ID and current state. It returns a queryset of matching Basket objects.

    Args:
        user_id (str): The unique identifier of the user whose baskets are to be retrieved.
        current_state (str): The current state of the baskets to filter (e.g., 'waiting', 'monitoring').

    Returns:
        QuerySet: A Django QuerySet containing Basket objects that match the specified user ID
        and current state. If no matches are found, an empty QuerySet is returned.
    """
    logger.info(f'In get_basket_details {user_id =}, {current_state =}')
    return Basket.objects.filter(user_id=user_id, current_state=current_state)


def update_basket(basket_id, basket_data):
    """
    Updates a Basket instance with the provided data. Only fields with non-null values
    are updated in the instance.

    Args:
        basket_id (int or str): The ID of the Basket instance to be updated.
        basket_data (dict): A dictionary containing the fields to update and their values.

    Returns:
        Basket: The updated Basket instance.

    Raises:
        Basket.DoesNotExist: If the Basket with the given ID does not exist.
        BasketNotFound: Custom exception raised if the basket is not found.
        Exception: For any other generic errors during the update process.
    """
    try:
        logger.info(f"Updating basket {basket_id =}, {basket_data =}")
        basket_instance = Basket.objects.get(id=basket_id)
        basket_data.pop('id', None)

        for key, value in basket_data.items():
            if value is not None:
                setattr(basket_instance, key, value)

        basket_instance.save()
        return Basket.objects.get(id=basket_id)
    except Basket.DoesNotExist as exc:
        logger.info(f"Basket with ID {basket_id} does not exist.")
        logger.exception(exc)
        raise BasketNotFound(message=f"Basket data not found for '{basket_id =}'. ") from exc

    except Exception as exc:
        logger.info(f"Error in update_basket {exc =}")
        logger.exception(exc)
        raise exc


def get_next_basket_state(instance):
    """
    Determines the next state of the basket based on the current status of the orders.

    Args:
        instance (Order): The order instance to check the current status.

    Returns:
        str: The next state of the basket, which can be one of the predefined
        states in BasketStates.
    """
    basket_orders = instance.basket.user_basket.all()

    # If any order has the status 'BUY', set the basket state to 'MONITORING'
    if any(order.current_status == OrderCurrentStatus.BUY.value for order in basket_orders):
        return BasketStates.MONITORING.value

    # If all orders have the status 'BUY_IN_PROGRESS', set the basket state to 'WAITING'
    if all(order.current_status == OrderCurrentStatus.BUY_IN_PROGRESS.value for order in basket_orders):
        return BasketStates.WAITING.value

    # If all orders have the status 'SELL', set the basket state to 'COMPLETE'
    if all(order.current_status == OrderCurrentStatus.SELL.value for order in basket_orders):
        return BasketStates.COMPLETE.value

    # If any order has the status 'SELL_IN_PROGRESS', set the basket state to 'MONITORING'
    if any(order.current_status == OrderCurrentStatus.SELL_IN_PROGRESS.value for order in basket_orders):
        return BasketStates.MONITORING.value

    # If all orders are either 'SELL' or 'SKIP', set the basket state to 'COMPLETE'
    if all(order.current_status in (OrderCurrentStatus.SELL.value, OrderCurrentStatus.SKIP.value)
           for order in basket_orders):
        return BasketStates.COMPLETE.value

    # If all orders have the status 'SKIP', set the basket state to 'COMPLETE'
    if all(order.current_status == OrderCurrentStatus.SKIP.value for order in basket_orders):
        return BasketStates.COMPLETE.value

    # Default case: if neither of the conditions are met, return 'WAITING'
    return BasketStates.WAITING.value


def update_basket_details(instance):
    """
    Updates the details of the basket associated with the given order instance.

    This function calculates the total buy and sell amounts in the basket by
    adding the corresponding amounts from the order instance. It also computes
    the profit target value based on the updated total buy amount and the profit
    target defined in the basket. The basket's current state is updated based on
    the order's current status.

    Args:
        instance (Order): The order instance containing the details required
        to update the basket. It should have the following attributes:
            - id: The unique identifier for the order.
            - basket: The basket associated with the order (must have 'id'
              and 'profit_target' attributes).
            - initial_amount: The buy amount associated with the order (used for
              calculating the total buy amount).
            - end_amount: The sell amount associated with the order (used for
              calculating the total sell amount).

    Raises:
        Basket.DoesNotExist: If the basket associated with the order does not
        exist in the database.

    Logs:
        Updates and errors related to the basket update process.
    """
    logger.info(f"Updating basket for Order {instance.id =}")
    profit_target_1_value = None
    profit_target_2_value = None
    order_obj = Order.objects.filter(basket=instance.basket.id)

    total_buy_amount = sum([order.initial_amount if order.initial_amount is not None else 0 for order in order_obj])
    total_sell_amount = sum([order.end_amount if order.end_amount is not None else 0 for order in order_obj])

    if instance.basket.profit_target_1:
        profit_target_1_value = total_buy_amount * (1 + (instance.basket.profit_target_1 or 0) / 100)
    if instance.basket.profit_target_2:
        profit_target_2_value = total_buy_amount * (1 + (instance.basket.profit_target_2 or 0) / 100)

    Basket.objects.filter(id=instance.basket.id).update(
        amount=total_buy_amount,
        end_amount=total_sell_amount,
        profit_target_1_value=profit_target_1_value,
        profit_target_2_value=profit_target_2_value,
        current_state=get_next_basket_state(instance)
    )

    logger.info(f"Basket updated: {instance.basket.id}, new buy amount: {total_buy_amount}, "
                f"new sell amount: {total_sell_amount}, new profit_target_1_value: {profit_target_1_value}, "
                f"new profit_target_2_value: {profit_target_2_value}")
