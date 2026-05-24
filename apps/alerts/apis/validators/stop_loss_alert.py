from rest_framework import serializers


class StopLossAlertQueryParamsValidator(serializers.Serializer):
    """Validator for Stop Loss Alert query parameters"""
    user_portfolio_id = serializers.IntegerField(
        required=True,
        help_text="User portfolio ID to check for stop loss alerts"
    )
