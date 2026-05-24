"""
basket.py

This module defines the serializers for the Basket model. It utilizes Django 
REST Framework's ModelSerializer to convert Basket model instances into JSON 
format and vice versa. This serializer is responsible for validating and 
serializing the fields of the Basket model when interacting with the API.
"""

from rest_framework import serializers

from apps.holdings.serializers.positions import PositionSerializer
from apps.portfolio.models import Basket, OrderInstruction
from apps.portfolio.serializers.order_instructions import OrderInstructionSerializer
from apps.portfolio.serializers.orders import OrderSerializer


class BasketSerializer(serializers.ModelSerializer):
    """
    Serializer for the Basket model.

    This serializer provides validation and serialization for the Basket model
    instances, ensuring that all required fields are properly handled when
    converting to and from JSON.

    Attributes:
        Meta (class): Contains the model and fields to be serialized.
    """

    class Meta:
        model = Basket
        fields = [
            "id",
            "user_id",
            "current_state",
            "broker",
            "model_id",
            "basket_type",
            "product_type",
            "payment_id",
            "recommendation_id",
            "exposure_amount",
            "user_allocation",
            "cash_ingested",
            "amount",
            "end_amount",
            "profit_target_1",
            "profit_target_1_value",
            "profit_target_2",
            "profit_target_2_value",
        ]


class BasketReadSerializer(serializers.ModelSerializer):
    """
    Serializer for the Basket model that provides a detailed representation
    of a basket including its related orders and instructions.

    This serializer includes the following fields:
    - id: Unique identifier of the basket.
    - user_id: Identifier of the user associated with the basket.
    - current_state: The current state of the basket.
    - model_id: Identifier for the associated model.
    - basket_type: Type of the basket (e.g., investment, savings).
    - product_type: Type of product the basket contains.
    - payment_id: Identifier for the associated payment transaction.
    - recommendation_id: Identifier for the associated recommendation.
    - user_allocation: Allocation details for the user.
    - cash_ingested: Amount of cash ingested into the basket.
    - amount: Total amount in the basket.
    - profit_target: Target profit for the basket.
    - profit_target_value: Value of the target profit.
    - orders: Related orders associated with this basket.
    - instructions: Instructions related to the orders in this basket.

    Methods:
        get_orders: Retrieves orders related to the basket instance.
        get_instructions: Retrieves instructions related to the orders of the basket instance.
    """

    orders = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()
    positions = serializers.SerializerMethodField()

    def get_orders(self, obj):
        """
        Retrieve orders related to the basket instance.

        Args:
            obj (Basket): The basket instance for which orders are retrieved.

        Returns:
            list: Serialized list of related Order instances.
        """
        orders = obj.user_basket.all()
        return OrderSerializer(orders, many=True).data

    def get_instructions(self, obj):
        """
        Retrieve instructions of the OrderInstruction related to the basket instance.

        Args:
            obj (Basket): The basket instance for which instructions are retrieved.

        Returns:
            list: Serialized list of related OrderInstruction instances.
        """
        order_instructions = OrderInstruction.objects.filter(order__basket=obj)
        return OrderInstructionSerializer(order_instructions, many=True).data

    def get_positions(self, obj):
        """
        Retrieves all positions associated with the given basket object
        and serializes them for response.

        Args:
            obj (Basket): The basket object for which positions are being retrieved.

        Returns:
            list: A list of serialized position data associated with the basket.

        This method utilizes the related name 'positions' to access all `Position`
        objects linked to the given `Basket`. It then serializes the queryset
        using the `PositionSerializer`.
        """
        positions = obj.positions.all()
        positions_data = PositionSerializer(positions, many=True).data
        orders = self.get_orders(obj)
        orders = {order['trading_symbol']: order for order in orders}
        for position in positions_data:
            symbol = position['symbol']
            if symbol in orders:
                position['buy_price'] = orders[symbol]['buy_price']
                position['leverage'] = orders[symbol]['leverage']

        return positions_data

    class Meta:
        model = Basket
        fields = [
            "id",
            "user_id",
            "current_state",
            "broker",
            "model_id",
            "basket_type",
            "product_type",
            "payment_id",
            "recommendation_id",
            "exposure_amount",
            "user_allocation",
            "cash_ingested",
            "amount",
            "end_amount",
            "profit_target_1",
            "profit_target_1_value",
            "pt1_hit",
            "pt1_hit_time",
            "profit_target_2",
            "profit_target_2_value",
            "pt2_hit",
            "pt2_hit_time",
            "orders",
            "instructions",
            "positions",
            "created_str",
            "modified_str",
            "last_notification_sent",
        ]
