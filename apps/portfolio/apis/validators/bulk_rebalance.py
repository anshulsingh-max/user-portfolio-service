from rest_framework import serializers


class BulkRebalanceParamsValidator(serializers.Serializer):
    fromCache = serializers.BooleanField(required=False, default=False)
    # Comma-separated string of states; we'll normalize this in `validate()`
    currentState = serializers.CharField(required=False, allow_blank=True)
    # List of user-portfolio IDs to fetch rebalances for
    userPortfolioIds = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True,
        max_length=200,
        allow_empty=False,
    )

    def validate_currentState(self, value):
        """Trim whitespace; keep empty as-is (means no filter)."""
        return value.strip() if isinstance(value, str) else value

    def validate(self, attrs):
        # Let DRF run field-level validation first
        attrs = super().validate(attrs)

        raw_states = attrs.get("currentState") or ""
        states = [s.strip() for s in raw_states.split(",") if s.strip()]
        # Attach parsed list for consumers; keep original for backwards compat
        attrs["current_states"] = states or None
        return attrs
