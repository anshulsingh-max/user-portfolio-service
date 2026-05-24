from rest_framework import serializers

from apps.alerts.constants import Asset
from apps.alerts.models import UserPortfolioThreshold


class UserPortfolioThresholdSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserPortfolioThreshold model.

    This serializer provides validation and serialization for the
    UserPortfolioThreshold model instances, ensuring that all required
    fields are properly handled when converting to and from JSON.

    Attributes:
        Meta (class): Contains the model and fields to be serialized.
    """

    class Meta:
        model = UserPortfolioThreshold
        fields = [
            "id",
            "portfolio_type",
            "portfolio_id",
            "side",
            "threshold_type",
            "target_pct",
            "target_value",
            "status",
            "source",
            "source_id",
            "effective_from",
            "reason",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified", "reason"]


class UserPortfolioThresholdReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the UserPortfolioThreshold model.

    This serializer ensures that all enum/choice fields are returned
    in their human-readable form only (no internal enum codes).
    """

    # threshold_type = serializers.CharField(source="get_threshold_type_display", read_only=True)
    # status = serializers.CharField(source="get_status_display", read_only=True)
    # source = serializers.CharField(source="get_source_display", read_only=True)
    threshold_type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    source = serializers.CharField(read_only=True)
    reason = serializers.CharField(read_only=True)

    class Meta:
        model = UserPortfolioThreshold
        fields = [
            "id",
            "portfolio_type",
            "portfolio_id",
            "side",
            "threshold_type",
            "target_pct",
            "target_value",
            "status",
            "source",
            "source_id",
            "effective_from",
            "effective_to",
            "reason",
            "created",
            "modified",
        ]
        read_only_fields = fields


class UserPortfolioThresholdWithHoldingsSerializer(UserPortfolioThresholdReadSerializer):
    """Extends :class:`UserPortfolioThresholdReadSerializer` to also return the
    associated ``HoldingThreshold`` rows for the portfolio.

    The serializer discovers holdings under the portfolio (excluding the
    synthetic *cash* symbol) and serialises all matching
    ``HoldingThreshold`` objects that share the same ``side`` and
    ``threshold_type``.  This avoids an explicit DB‐level FK while still
    grouping relevant data for the API consumer.
    """

    holding_thresholds = serializers.SerializerMethodField()

    def get_holding_thresholds(self, obj):
        """Return serialised holding-level thresholds linked to *obj*."""
        from apps.holdings.models.holdings import Holding
        from apps.alerts.models.holding_threshold import HoldingThreshold
        from apps.alerts.serializers.holding_threshold import HoldingThresholdReadSerializer

        try:
            portfolio_id_int = int(obj.portfolio_id)
        except (TypeError, ValueError):
            return []

        # Fetch holdings, exclude 'cash', and map symbols to str explicitly
        holding_ids = [
            str(symbol) for symbol in Holding.objects.filter(user_portfolio=portfolio_id_int)
            .exclude(symbol=Asset.CASH.value)
            .values_list("id", flat=True)
        ]

        if not holding_ids:
            return []

        extra_filters = self.context.get("filters", {})

        ht_qs = (
            HoldingThreshold.objects.filter(
                holding_id__in=holding_ids,
                side=obj.side,
                **({"status": extra_filters.get("status")} if extra_filters.get("status") else {})
            )
            .order_by("-effective_from")
        )
        return HoldingThresholdReadSerializer(ht_qs, many=True).data

    class Meta(UserPortfolioThresholdReadSerializer.Meta):
        fields = UserPortfolioThresholdReadSerializer.Meta.fields + [
            "holding_thresholds",
        ]
