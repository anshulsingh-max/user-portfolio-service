"""
    Holdings serializer
"""
from rest_framework import serializers

from apps.holdings.models.holdings import Holding


class HoldingSerializer(serializers.ModelSerializer):
    """
    Holding Serializer
    """
    product_type = serializers.CharField(source='user_portfolio.product_type', read_only=True)
    strategy = serializers.CharField(source='user_portfolio.strategy', read_only=True)

    class Meta:
        model = Holding
        fields = [
            "id",
            "user_portfolio",
            "symbol",
            "quantity",
            "avg_buy_price",
            "portfolio_id",
            "product_type",
            "strategy"
        ]


class AllUsersHoldingSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user_portfolio.user_id')
    product_type = serializers.CharField(source='user_portfolio.product_type', read_only=True)
    strategy = serializers.CharField(source='user_portfolio.strategy', read_only=True)

    class Meta:
        model = Holding
        fields = [
            "id",
            "user_portfolio",
            "symbol",
            "quantity",
            "avg_buy_price",
            "user_portfolio_id",
            "user_id",
            "product_type",
            "strategy"
        ]
