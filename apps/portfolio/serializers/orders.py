"""
orders.py

This module contains serializers for the Order model. These serializers are responsible for
validating and transforming the Order data into a format that can be easily rendered into JSON
or other content types, and for converting incoming data into Python objects before saving
to the database.

The serializers also handle any custom logic related to fields validation or transformation
of the Order model.
"""

from rest_framework import serializers
from apps.portfolio.models import Order


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the Order model.

    This serializer is used to convert Order instances into JSON format for API responses,
    and to validate incoming data when creating or updating Order instances. It includes
    fields for the basket, trading symbol, buy and sell prices, the current state of the order,
    and other relevant attributes like amount, stop loss, and leverage.

    Fields:
        - basket (ForeignKey): The associated basket for the order.
        - trading_symbol (CharField): The trading symbol related to the order.
        - buy_price (FloatField): The price at which the order was bought (optional).
        - sell_price (FloatField): The price at which the order was sold (optional).
        - current_status (CharField): The current status of the order, based on predefined choices.
        - amount (FloatField): The total value associated with the order.
        - stop_loss (FloatField): The stop-loss value for the order (optional).
        - leverage (FloatField): The leverage applied to the order (optional).
    """

    class Meta:
        model = Order
        fields = [
            'basket',
            'trading_symbol',
            'buy_price',
            'sell_price',
            'current_status',
            'initial_amount',
            'end_amount',
            'stop_loss',
            'stop_loss_hit',
            'stop_loss_hit_time',
            'last_notification_sent',
            'leverage',
            'created_str',
            'modified_str'
        ]
