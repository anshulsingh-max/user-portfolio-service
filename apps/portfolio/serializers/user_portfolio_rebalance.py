from rest_framework import serializers
from apps.portfolio.models import UserPortfolioRebalance
from apps.portfolio.serializers.portfolio_rebalance_transaction import ReadPortfolioRebalanceTransactionSerializer


class UserPortfolioRebalanceSerializer(serializers.ModelSerializer):
    """
    User Portfolio Rebalance Serializer
    """
    user_inputs = serializers.JSONField()

    class Meta:
        model = UserPortfolioRebalance
        fields = [
            "user_portfolio",
            "type",
            "states",
            "current_state",
            "rebalance_id",
            "user_inputs",
            "cash_ingested",
            "transaction_type",
            "transaction",
            "metadata",
            "proxy",
            "proxy_id",
            "rebalance_strategy"
        ]


class ReadUserPortfolioRebalanceSerializer(serializers.ModelSerializer):
    """
    User Portfolio Rebalance Serializer
    """
    user_inputs = serializers.JSONField()
    rebalance_transactions = serializers.SerializerMethodField()

    def get_rebalance_transactions(self, obj):
        """
            User Instructions of the PortfolioRebalanceTransaction
            :return:
        """
        portfolio_rebalance_transactions = obj.portfolio_rebalance_transactions.all()
        portfolio_rebalance_transactions = ReadPortfolioRebalanceTransactionSerializer(portfolio_rebalance_transactions,
                                                                                       many=True).data
        return portfolio_rebalance_transactions

    class Meta:
        model = UserPortfolioRebalance
        fields = [
            "id",
            "user_portfolio",
            "type",
            "states",
            "current_state",
            "rebalance_id",
            "user_inputs",
            "cash_ingested",
            "cash_carry_forward",
            "transaction_type",
            "transaction",
            "total_invested_value",
            "created",
            "modified",
            "metadata",
            "rebalance_transactions",
            "buy_value",
            "sell_value",
            "rebalance_type",
            "proxy",
            "proxy_id",
            "rebalance_strategy",
            "reason",
        ]
