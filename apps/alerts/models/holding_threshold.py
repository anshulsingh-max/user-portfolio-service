from django.db import models
from django.db.models import Q
from django_extensions.db.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from apps.alerts.constants import PortfolioThresholdTypes, Status, ThresholdSource, PortfolioSides


class HoldingThreshold(TimeStampedModel):
    """
    Stock/Holding-level threshold rule (e.g., Profit Target, Stop Loss).

    Thresholds define conditions that trigger stock-level actions such as notifications,
    position exits, or manual overrides.

    Either a percentage-based threshold (`target_pct`) or an absolute value-based
    threshold (`target_value`) must be set, but not both.

    Attributes:
        holding_type (str):
            Type/category of holding (e.g., "STOCK", "ETF", etc.) to identify the target entity.

        holding_id (str):
            Identifier of the holding (e.g., ticker symbol or internal ID).

        side (str):
            Position side for which this threshold applies (long/short). Defined by `PortfolioSides`.

        threshold_type (str):
            Type of threshold rule (e.g., Profit Target, Stop Loss). Defined by `HoldingThresholds`.

        target_pct (Float):
            Percentage-based threshold applied for this rule.

        target_value (Float):
            Absolute value-based threshold applied for this rule.

        status (str):
            Current status of the threshold (e.g., Active, Inactive). Defined by `Status`.

        source (str):
            Origin of the threshold definition (User, Admin, Dealer). Defined by `ThresholdSource`.

        effective_from (datetime):
            Timestamp when this threshold became active.

        effective_to (datetime | None):
            Optional timestamp when this threshold expires or is deactivated.

        triggered_at (datetime | None):
            Timestamp when this threshold was first hit/triggered.

        last_notification_sent_at (datetime | None):
            Timestamp of the last notification sent for this threshold hit.

        history (HistoricalRecords):
            Historical audit log for changes to this object.
    """

    class Meta:
        db_table = "holding_threshold"
        verbose_name = "Holding Threshold"
        verbose_name_plural = "Holding Thresholds"
        indexes = [
            models.Index(fields=["holding_type", "holding_id"]),
            models.Index(fields=["holding_type", "holding_id", "side"]),
            models.Index(fields=["holding_type", "holding_id", "threshold_type"]),
            models.Index(
                fields=["holding_type", "holding_id", "side", "threshold_type"],
                name="idx_holding_threshold_active",
                condition=Q(status=Status.ACTIVE)
            ),
        ]

    holding_type = models.CharField(
        max_length=50,
        blank=False,
        help_text="Type/category of holding (e.g., STOCK, ETF)"
    )

    holding_id = models.CharField(
        max_length=100,
        blank=False,
        help_text="Identifier of the holding (ticker symbol or internal ID)"
    )

    side = models.CharField(
        max_length=10,
        choices=PortfolioSides.choices,
        blank=False,
        help_text="Position side this threshold applies to (long/short)"
    )

    threshold_type = models.CharField(
        max_length=20,
        choices=PortfolioThresholdTypes.choices,
        blank=False,
        help_text="Type of threshold rule (Profit Target/Stop Loss)"
    )

    target_pct = models.FloatField(
        null=True,
        blank=True,
        help_text="Percentage threshold (e.g. 12.50%)"
    )

    target_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Absolute value threshold in INR (up to ~1000 crore)"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        blank=False,
        help_text="Status of the rule"
    )

    source = models.CharField(
        max_length=10,
        choices=ThresholdSource.choices,
        default=ThresholdSource.USER,
        blank=False,
        help_text="Origin of the rule (User/Admin/Dealer)"
    )

    effective_from = models.DateTimeField(auto_now_add=True)
    effective_to = models.DateTimeField(null=True, blank=True)

    triggered_at = models.DateTimeField(null=True, blank=True)
    last_notification_sent_at = models.DateTimeField(null=True, blank=True)

    reason = models.TextField(null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.get_threshold_type_display()} Threshold for {self.holding_type}:{self.holding_id} ({self.side})"
