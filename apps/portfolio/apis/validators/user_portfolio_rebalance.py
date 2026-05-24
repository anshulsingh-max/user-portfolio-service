"""
    API Request Validators
"""

from rest_framework import serializers

from apps.portfolio.constants import RebalanceTypes, CashTransaction, States, RebalanceTransactionTypes, Proxy, \
    RebalanceTransactionStates
from apps.portfolio.constants import RebalanceStrategy


class UserPortfolioRebalanceParamsValidator(serializers.Serializer):
    """
        Post UserPortfolioRebalance Request Params Validator
    """
    user_portfolio = serializers.IntegerField(required=True, min_value=1)
    type = serializers.ChoiceField(required=True, choices=RebalanceTypes.CHOICES.value)
    rebalance_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    user_inputs = serializers.JSONField(default={})
    cash_ingested = serializers.FloatField(required=False, allow_null=True)
    transaction_type = serializers.ChoiceField(required=True, choices=CashTransaction.CHOICES.value)
    transaction = serializers.IntegerField(required=False, allow_null=True)
    metadata = serializers.JSONField(default={}, required=False)
    proxy = serializers.ChoiceField(choices=Proxy.CHOICES.value, required=False, default=Proxy.USER.value)
    proxy_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    instruction_url = serializers.URLField(default=None, required=False, allow_null=True, allow_blank=True)
    rebalance_strategy = serializers.ChoiceField(required=False, default=None, choices=RebalanceStrategy.choices())


class GetUserPortfolioRebalanceParamsValidator(serializers.Serializer):
    """
        Post UserPortfolioRebalance Request Params Validator
    """
    current_state = serializers.CharField(required=True)

    def validate(self, data):
        data['current_state'] = data['current_state'].split(",")
        return data


class GetRebalanceOrdersParamsValidator(serializers.Serializer):
    """
        Post GetRebalanceOrders Request Params Validator
    """
    user_portfolio_rebalance_id = serializers.IntegerField(required=True)
    type = serializers.ChoiceField(choices=RebalanceTransactionTypes.CHOICES.value, required=True)


class UpdateUserPortfolioRebalanceParamsValidator(serializers.Serializer):
    """
        Update UserPortfolioRebalance Request Params Validator
    """
    cash_ingested = serializers.FloatField(required=False, allow_null=True)
    transaction = serializers.IntegerField(required=False, allow_null=True)
    instruction_url = serializers.URLField(default=None, required=False, allow_null=True, allow_blank=True)


class ManuallyCompleteRebalanceParamsValidation(serializers.Serializer):

    status = serializers.ChoiceField(default=RebalanceTransactionStates.MANUALLY_COMPLETED.value,
                                     choices=RebalanceTransactionStates.MANUALLY_COMPLETED_STATUS_CHOICES.value,
                                     required=False)


class ManualCompleteLatestRebalanceTransactionValidator(serializers.Serializer):
    """Validator to mark the latest eligible transaction as manually completed."""

    user_portfolio_id = serializers.IntegerField(required=True, min_value=1)


class CloseRebalanceParamsValidator(serializers.Serializer):
    """Validator for closing a rebalance."""
    rebalance_id = serializers.IntegerField(required=True, min_value=1)
