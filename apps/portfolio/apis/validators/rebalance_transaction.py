"""
    API Request Validators
"""

from rest_framework import serializers


class RebalanceTransactionParamsValidator(serializers.Serializer):
    """
        Post RebalanceTransaction Request Params Validator
    """
    user_portfolio_rebalance_id = serializers.IntegerField(required=True, source="portfolio_rebalance")
    allocation_quantity = serializers.JSONField(required=True)
    rebalance_json = serializers.JSONField(required=True, source="user_rebalance_json")


class UpdatePortfolioTransactionParamsValidator(serializers.Serializer):
    """
        Put Portfolio Rebalance Transaction Request Params Validator
    """

    type = serializers.CharField(required=False)
    current_state = serializers.CharField(required=False)
