"""
Serializer for the OrderInstruction model.

This serializer is responsible for converting the OrderInstruction model instances
into JSON format for API responses and for validating incoming data for deserialization
and object creation.

Fields:
    orders (ForeignKey): A reference to the related orders.
    trade_placement_id (str): The ID associated with the placement of the trade.
    order_tag (str): A tag used to identify the order.
    symbol (str): The trading symbol for the financial instrument.
    quantity (float): The total quantity of the financial instrument in the order.
    filled_quantity (float): The quantity of the order that has been filled.
    order_price (float): The price at which the order is placed.
    side (str): The side of the trade (buy/sell).
    source (str): The source of the order.
    value (float): The total value of the order.
    status (str): The current status of the order.
    reason (str): The reason associated with the order status (if any).

Meta:
    model (OrderInstruction): The model associated with this serializer.
    fields (list): The fields that are serialized and deserialized in API interactions.
"""
from rest_framework import serializers

from apps.portfolio.models import OrderInstruction


class OrderInstructionSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderInstruction
        fields = [
            'id',
            'order',
            'trade_placement_id',
            'order_tag',
            'symbol',
            'quantity',
            'filled_quantity',
            'order_price',
            'side',
            'source',
            'value',
            'status',
            'reason',
            'created_str',
            'modified_str'
        ]
