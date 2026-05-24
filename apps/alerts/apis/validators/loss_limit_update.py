from rest_framework import serializers


class LossLimitUpdateValidator(serializers.Serializer):
    """Validator for Loss Limit Updated notification request"""
    user_portfolio_id = serializers.IntegerField(
        required=True,
        help_text="User portfolio ID to notify"
    )
    loss_limit = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Optional loss limit override"
    )