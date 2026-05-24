"""
    API Request Validators
"""

from rest_framework import serializers

from apps.portfolio.constants import Side, OrderStatus


class UpdateTradeDetailsParamsValidator(serializers.Serializer):
    """
        Put Update Trade Details Request Params Validator
    """
    trade_placement_id = serializers.IntegerField(required=True, allow_null=True)
    order_tag = serializers.CharField(required=True)
    symbol = serializers.CharField(required=True)
    quantity = serializers.FloatField(required=True)
    filled_quantity = serializers.FloatField(required=True)
    side = serializers.ChoiceField(choices=Side.CHOICES.value)
    value = serializers.FloatField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=OrderStatus.CHOICES.value)
    reason = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    retry_allowed = serializers.BooleanField(required=False, allow_null=True)
    price = serializers.FloatField(required=False, allow_null=True)
