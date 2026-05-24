from rest_framework import serializers

from apps.alerts.constants import PortfolioThresholdTypes, Status, ThresholdSource, PortfolioSides


class HoldingThresholdParamsValidator(serializers.Serializer):
    """Validate request body for creating a HoldingThreshold."""

    holding_type = serializers.CharField(required=True, max_length=50)
    holding_id = serializers.CharField(required=True, max_length=100)
    side = serializers.ChoiceField(required=True, choices=PortfolioSides.choices)
    threshold_type = serializers.ChoiceField(required=True, choices=PortfolioThresholdTypes.choices)
    target_pct = serializers.FloatField(required=False)
    target_value = serializers.FloatField(required=False)
    status = serializers.ChoiceField(required=True, choices=Status.choices)
    source = serializers.ChoiceField(required=True, choices=ThresholdSource.choices)

    def validate(self, attrs):
        pct = attrs.get("target_pct")
        val = attrs.get("target_value")
        if pct is None and val is None:
            raise serializers.ValidationError("Either target_pct or target_value must be provided.")
        if pct is not None and val is not None:
            raise serializers.ValidationError("Provide only one of target_pct or target_value, not both.")
        return attrs


class HoldingThresholdQueryParamsValidator(serializers.Serializer):
    """Validate query params for fetching HoldingThresholds."""

    holding_type = serializers.CharField(required=True)
    holding_id = serializers.CharField(required=False)
    side = serializers.ChoiceField(choices=PortfolioSides.choices, required=False)
    threshold_type = serializers.ChoiceField(choices=PortfolioThresholdTypes.choices, required=False)
    status = serializers.ChoiceField(choices=Status.choices, required=False)
    source_id = serializers.CharField(required=False)

    @property
    def filters(self):
        if not hasattr(self, "validated_data"):
            raise AttributeError("Call .is_valid() before accessing filters")
        return {k: v for k, v in self.validated_data.items() if v is not None}


class UpdateHoldingThresholdSerializer(serializers.Serializer):
    """Validate fields for updating a HoldingThreshold (PUT)."""

    id = serializers.IntegerField(required=True)
    target_pct = serializers.FloatField(required=False)
    target_value = serializers.FloatField(required=False)
    status = serializers.ChoiceField(choices=Status.choices, required=False)
    source = serializers.ChoiceField(choices=ThresholdSource.choices, required=False)
    source_id = serializers.CharField(required=False)

    def validate(self, attrs):
        pct = attrs.get("target_pct")
        val = attrs.get("target_value")
        if pct is not None and val is not None:
            raise serializers.ValidationError("Provide only one of target_pct or target_value, not both.")
        return attrs
