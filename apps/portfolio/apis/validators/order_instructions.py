"""
This module contains validators related to order instructions in the portfolio application.

Validators:
    CreateOrderInstructionsValidator: A serializer to validate the fields required for creating
    order instructions, ensuring that all required fields are present and valid.

    The module is part of the `validators` package and is used to validate incoming data
    related to order instructions before processing or persisting it in the system.

Attributes:
    Side (Enum): An enumeration that defines the possible sides for a trade, such as 'buy' or 'sell'.
"""

from rest_framework import serializers

from apps.portfolio.constants import Side, OrderStatus, OrderInstructionSources


class OrderInstructionsValidator(serializers.Serializer):
    """
    A serializer for validating the fields required to create order instructions.

    Fields:
        order_id (int): The unique identifier for the order.
        symbol (str): The trading symbol for the financial instrument being ordered.
        quantity (float): The quantity of the financial instrument to be traded.
        side (str): The side of the trade, which must be one of the predefined choices
            ('buy' or 'sell') from the `Side` enum.
        source (str): The source of the order, which must be one of the predefined choices
            ('normal' or 'reconcile').

    Validations:
        - Ensures that `order_id` is an integer.
        - Ensures that `symbol` is a valid string.
        - Ensures that `quantity` is a float representing the number of instruments.
        - Ensures that `side` is a valid choice from the `Side` enum (either 'buy' or 'sell').
        - Ensures that `source` is a valid choice (either 'normal' or 'reconcile').
    """

    order_id = serializers.IntegerField()
    symbol = serializers.CharField()
    quantity = serializers.FloatField()
    side = serializers.ChoiceField(choices=Side.CHOICES.value)
    source = serializers.ChoiceField(choices=OrderInstructionSources.CHOICES.value,
                                     required=False,
                                     default=OrderInstructionSources.MANUAL.value)


class CreateOrderInstructionsValidator(serializers.Serializer):
    """
    A serializer for validating a list of order instructions.

    Fields:
        instructions (list): A list of order instructions where each instruction is validated by
                             the OrderInstructionValidator.

    Validations:
        - Ensures that `instructions` is a list of valid order instruction objects.
    """
    instructions = serializers.ListField(
        child=OrderInstructionsValidator()
    )


class UpdateOrderInstructionsValidator(serializers.Serializer):
    """
    Serializer to validate update order instructions for a trade placement.

    Fields:
        - trade_placement_id (int): The unique ID of the trade placement.
            - Required: Yes
            - Allows Null: Yes
        - order_tag (str): A tag or identifier for the order.
            - Required: Yes
        - symbol (str): The trading symbol for the order (e.g., "AAPL", "GOOG").
            - Required: Yes
        - quantity (float): The total quantity of the order.
            - Required: Yes
        - price (float): The price of the order at which it was executed.
            - Required: False
            - Allow Null: Yes
        - filled_quantity (float): The quantity of the order that has already been filled.
            - Required: Yes
        - side (str): The side of the order (e.g., "buy" or "sell").
            - Required: Yes
            - Choices: Defined in `Side.CHOICES`
        - source (str): The source of the order (e.g., "normal" or "reconcile").
            - Required: No
            - Choices: Defined in ["normal", "reconcile"]
        - value (float): The value of the order (optional).
            - Required: No
            - Allows Null: Yes
        - status (str): The current status of the order.
            - Required: Yes
            - Choices: Defined in `OrderStatus.CHOICES`
        - reason (str): The reason for the current order status (optional).
            - Required: No
            - Allows Null: Yes
            - Allows Blank: Yes

    Usage:
        This serializer is used to validate input data when updating order instructions
        in trade-related operations. It ensures that all necessary fields are provided
        and conform to the expected sources and choices.

    Example:
        data = {
            "trade_placement_id": 123,
            "order_tag": "ORDER_001",
            "symbol": "AAPL",
            "quantity": 100.0,
            "filled_quantity": 50.0,
            "side": "buy",
            "source": "normal",
            "value": 15000.0,
            "status": "completed",
            "reason": "Order partially filled"
        }
        serializer = UpdateOrderInstructionsValidator(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
    """
    trade_placement_id = serializers.IntegerField(required=True, allow_null=True)
    order_tag = serializers.CharField(required=True)
    symbol = serializers.CharField(required=True)
    quantity = serializers.FloatField(required=True)
    price = serializers.FloatField(required=False, allow_null=True)
    filled_quantity = serializers.FloatField(required=True)
    side = serializers.ChoiceField(choices=Side.CHOICES.value)
    source = serializers.ChoiceField(choices=OrderInstructionSources.CHOICES.value,
                                     required=False,
                                     default=OrderInstructionSources.MANUAL.value)
    value = serializers.FloatField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=OrderStatus.CHOICES.value)
    reason = serializers.CharField(allow_null=True, allow_blank=True, required=False)
