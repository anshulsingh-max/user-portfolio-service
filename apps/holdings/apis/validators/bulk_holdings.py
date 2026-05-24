from rest_framework import serializers


class BulkHoldingsParamsValidator(serializers.Serializer):
    userPortfolioIds = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        max_length=200,
        required=True,
    )
    fromCache = serializers.BooleanField(required=False, default=False)


class BulkHoldingsResponseSerializer(serializers.Serializer):
    # Mapping from user_portfolio_id (int) to list of holding objects
    holdings = serializers.DictField(child=serializers.ListField())

