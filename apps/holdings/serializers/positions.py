"""
Serializers for the holdings app.

This module contains serializers for converting complex data types, such as
querysets and model instances, into native Python data types that can then
be easily rendered into JSON, XML, or other content types.
"""

from rest_framework import serializers
from apps.holdings.models import Position


class PositionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Position model.

    This serializer is used to convert Position model instances into JSON
    format and vice versa. It includes fields for basket, symbol, and
    quantity, which represent the key attributes of a position in a user's
    portfolio.
    """

    class Meta:
        model = Position
        fields = [
            "basket",
            "symbol",
            "quantity"
        ]

class PositionsReadSerializer(PositionSerializer):
    """
    Serializer for the Position model.

    This serializer is used to convert Position model instances into JSON
    format and vice versa. It includes fields for basket, symbol, and
    quantity, which represent the key attributes of a position in a user's
    portfolio.
    """
    user_id = serializers.CharField(source='basket.user_id')
    class Meta:
        model = Position
        fields = [
            "basket",
            "symbol",
            "quantity",
            "user_id"
        ]
