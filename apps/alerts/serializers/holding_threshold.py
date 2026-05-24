from rest_framework import serializers

from apps.alerts.models import HoldingThreshold


class HoldingThresholdSerializer(serializers.ModelSerializer):
    """Serializer for the HoldingThreshold model (create/update)."""

    class Meta:
        model = HoldingThreshold
        fields = [
            "id",
            "holding_type",
            "holding_id",
            "side",
            "threshold_type",
            "target_pct",
            "target_value",
            "status",
            "source",
            "reason",
            "effective_from",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified", "reason"]


class HoldingThresholdReadSerializer(serializers.ModelSerializer):
    """Read-only serializer returning human-readable enum values."""

    # threshold_type = serializers.CharField(source="get_threshold_type_display", read_only=True)
    # status = serializers.CharField(source="get_status_display", read_only=True)
    # source = serializers.CharField(source="get_source_display", read_only=True)
    threshold_type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    source = serializers.CharField(read_only=True)
    reason = serializers.CharField(read_only=True)

    class Meta:
        model = HoldingThreshold
        fields = [
            "id",
            "holding_type",
            "holding_id",
            "side",
            "threshold_type",
            "target_pct",
            "target_value",
            "status",
            "source",
            "reason",
            "effective_from",
            "effective_to",
            "created",
            "modified",
        ]
        read_only_fields = fields
