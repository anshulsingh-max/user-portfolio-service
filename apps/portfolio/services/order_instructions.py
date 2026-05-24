"""
Service functions for handling the creation of order instructions.

These functions provide business logic for creating and managing order instructions
related to a user's orders. They handle serialization, validation, and saving data
to the database.

Functions:
    create_order_instructions: Serializes and creates an OrderInstruction instance.
    create_instructions: Creates and saves order instructions based on basket allocations.
"""

import logging

from django.db.models import OuterRef, Subquery, Max, F

from apps.portfolio.constants import OrderStatus, OrderInstructionSources
from apps.portfolio.models import OrderInstruction
from apps.portfolio.serializers.order_instructions import OrderInstructionSerializer

logger = logging.getLogger(__name__)


def create_order_instructions(order_instructions):
    """
    Creates an OrderInstruction instance from the provided data.

    This function takes a dictionary of order instruction details, generates an
    order tag, and serializes the data before saving it to the database.

    Args:
        order_instructions (dict): The dictionary containing order instruction data.
            Expected keys include 'order_id', 'symbol', and 'side'.

    Returns:
        OrderInstruction: The saved OrderInstruction instance.

    Raises:
        ValidationError: If the data is invalid and does not pass serializer validation.
    """
    data = []
    for order_instruction in order_instructions:
        order_tag = f"{order_instruction.get('order_id')}_{order_instruction.get('symbol')}_{order_instruction.get('side')}"
        order_instruction['order_tag'] = order_tag
        order_instruction['order'] = order_instruction['order_id']
        order_instruction['source'] = order_instruction['source']

        ser = OrderInstructionSerializer(data=order_instruction)
        if ser.is_valid(raise_exception=True):
            instance = ser.save()
            data.append(instance)
    return data


def create_instructions(instance):
    """
    Creates and saves OrderInstruction instances based on basket allocations.

    This function iterates over a basket's user allocations and creates an
    OrderInstruction for each allocation related to the order instance.

    Args:
        instance (Order): The order instance for which instructions are created.

    Side Effects:
        Saves OrderInstruction instances to the database.
    """
    logger.info(f"In create instructions for Order {instance.id}")
    allocations = instance.basket.user_allocation

    for allocation in allocations:
        order_tag = f"{instance.id}_{allocation.get('symbol')}_{allocation.get('side')}"
        trading_symbol = allocation.get('symbol')
        quantity = allocation.get('quantity')
        side = allocation.get('side')

        if trading_symbol == instance.trading_symbol:
            order_instruction = OrderInstruction(
                order=instance,
                order_tag=order_tag,
                symbol=trading_symbol,
                quantity=quantity,
                side=side
            )
            order_instruction.save()
            logger.info(f"OrderInstruction created for Order {instance.id} with order_tag {order_tag}")


def get_cancelled_instructions(basket_id):
    """
    Retrieve the latest canceled order instructions for each order in a specific basket.

    This function fetches the most recent canceled order instruction for each
    order linked to the provided `basket_id`. It uses a subquery to identify
    the latest canceled instruction based on the creation timestamp.

    Args:
        basket_id (int): The ID of the basket for which to fetch canceled instructions.

    Returns:
        list: A list of serialized canceled order instructions for the given basket.
    """
    latest_cancelled_instructions = (
        OrderInstruction.objects
        .annotate(latest_created=Max('order__user_order__created'))
        .filter(created=F('latest_created'),
                status=OrderStatus.CANCEL.value,
                order__basket__id=basket_id)
    ).exclude(source=OrderInstructionSources.SKIP.value)
    return latest_cancelled_instructions


def create_retry_instructions(cancelled_instructions):
    """
    Create new retry instructions from a list of canceled instructions.

    This function takes a list of canceled order instructions, recreates
    each one by extracting the necessary fields, and then validates and saves
    them as new `OrderInstruction` instances.

    Args:
        cancelled_instructions (list): A list of canceled order instruction data.

    Returns:
        list: A list of serialized newly created retry order instructions.
    """
    data = []

    for instruction in cancelled_instructions:
        order_tag = instruction.order_tag

        instruction.pk = None
        instruction.trade_placement_id = None
        instruction.status = OrderStatus.WAITING.value
        instruction.reason = None
        instruction.order_tag = order_tag
        instruction.source = OrderInstructionSources.RETRY.value
        instruction.save()

        serialized_instruction = OrderInstructionSerializer(instruction)
        data.append(serialized_instruction.data)

    return data
