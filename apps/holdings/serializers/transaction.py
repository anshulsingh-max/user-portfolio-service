"""
    Holdings serializer
"""
from rest_framework import serializers

from apps.holdings.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """
    Transaction Serializer
    """
    class Meta:
        model = Transaction
        fields = [
            "user_portfolio",
            "source",
            "target",
            "amount",
            "type",
            "current_state"
        ]
