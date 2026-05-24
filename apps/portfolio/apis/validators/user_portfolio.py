"""
    API request validators
"""

from rest_framework import serializers

from apps.portfolio.constants import UserPortfolioStatus, InvestmentStatus, BrokerEnum, Proxy, ProductTypes, Strategy


class UserPortfolioParamsValidator(serializers.Serializer):
    """
        POST User Portfolio Params Validator
    """
    user_id = serializers.CharField(max_length=100, required=True)
    name = serializers.CharField(max_length=100, required=True)
    portfolio_id = serializers.CharField(max_length=100, required=True)
    status = serializers.ChoiceField(choices=UserPortfolioStatus.CHOICES.value)
    subscription_id = serializers.CharField(max_length=100, required=True)
    broker = serializers.ChoiceField(choices=BrokerEnum.CHOICES.value)
    proxy = serializers.ChoiceField(choices=Proxy.CHOICES.value, required=False, default=Proxy.USER.value)
    proxy_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    product_type = serializers.ChoiceField(choices=ProductTypes.CHOICES.value,
                                           required=False, default=ProductTypes.EQUITY.value)
    strategy = serializers.ChoiceField(choices=Strategy.CHOICES.value,
                                       required=False, default=Strategy.REBALANCE.value)
    expected_investment = serializers.FloatField(required=False, allow_null=True)


class UserPortfolioQueryParamsValidator(serializers.Serializer):
    """
        GET User Portfolio Query Params Validator
    """
    status = serializers.ChoiceField(choices=UserPortfolioStatus.CHOICES.value, required=False)
    investment_status = serializers.ChoiceField(choices=InvestmentStatus.CHOICES.value, required=False)
    user_id = serializers.CharField(max_length=100, required=False)
    portfolio_id = serializers.CharField(required=False)
    broker = serializers.ChoiceField(choices=BrokerEnum.CHOICES.value, required=False)
    subscription_id = serializers.CharField(required=False)
    product_type = serializers.ChoiceField(choices=ProductTypes.CHOICES.value,
                                           required=False)
    strategy = serializers.ChoiceField(choices=Strategy.CHOICES.value,
                                       required=False)


class UserPortfolioReqParamsValidator(serializers.Serializer):
    """
        GET User Portfolio by id validator
    """
    id = serializers.IntegerField(required=True)


class UserPortfolioUpdateValidator(serializers.Serializer):
    """
        UPDATE User Portfolio by id validator
    """
    user_id = serializers.CharField(max_length=100, required=False)
    name = serializers.CharField(max_length=100, required=False)
    portfolio_id = serializers.CharField(max_length=100, required=False)
    status = serializers.ChoiceField(choices=UserPortfolioStatus.CHOICES.value, required=False)
    id = serializers.IntegerField(required=True)
    deactivated_reason = serializers.CharField(required=False)
    proxy = serializers.ChoiceField(choices=Proxy.CHOICES.value, required=False, default=Proxy.USER.value)
    proxy_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    product_type = serializers.ChoiceField(choices=ProductTypes.CHOICES.value,
                                           required=False)
    strategy = serializers.ChoiceField(choices=Strategy.CHOICES.value,
                                       required=False)


class UserPortfolioUpdateBySubscriptionIdValidator(serializers.Serializer):
    """
    UPDATE User Portfolio by subscription_id validator
    """
    user_id = serializers.CharField(max_length=100, required=False)
    name = serializers.CharField(max_length=100, required=False)
    portfolio_id = serializers.CharField(max_length=100, required=False)
    status = serializers.ChoiceField(choices=UserPortfolioStatus.CHOICES.value, required=False)
    subscription_id = serializers.CharField(max_length=100, required=True)
    proxy = serializers.ChoiceField(choices=Proxy.CHOICES.value, required=False, default=Proxy.USER.value)
    proxy_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    product_type = serializers.ChoiceField(choices=ProductTypes.CHOICES.value,
                                           required=False)
    strategy = serializers.ChoiceField(choices=Strategy.CHOICES.value,
                                       required=False)


class UserPortfolioPositionParamsValidator(serializers.Serializer):
    user_id = serializers.CharField(max_length=100, required=False)
    basket_id = serializers.CharField(max_length=100, required=False)


class UserPortfolioSummaryParamsValidator(serializers.Serializer):
    """
    Serializer to validate query parameters for fetching user portfolio summary.

    Fields:
        - user_id (str): ID of the user.
        - broker (str): Broker associated with the portfolio.
        - product_type (str): Product type (e.g., 'mtf', 'equity', etc.).
    """
    user_id = serializers.CharField(max_length=100)
    broker = serializers.CharField(max_length=100)
    product_type = serializers.ChoiceField(choices=ProductTypes.CHOICES.value)
