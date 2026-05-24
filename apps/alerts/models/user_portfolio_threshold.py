from django.db import models
from django.db.models import Q
from django_extensions.db.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from apps.alerts.constants import PortfolioThresholdTypes, Status, ThresholdSource, PortfolioSides


class UserPortfolioThreshold(TimeStampedModel):
    """
    Represents a threshold rule (e.g., Profit Target, Stop Loss) configured for a
    portfolio-like entity. Thresholds define conditions that trigger portfolio-level
    actions such as notifications, position exits, or locking the portfolio.

    Either a percentage-based threshold (`target_pct`) or an absolute value-based
    threshold (`target_value`) must be set, but not both.

    Attributes:
        portfolio_type (str):
            Type of portfolio-like entity this threshold applies to (e.g., "USER_PORTFOLIO",
            "BASKET", "STRATEGY"). Used with `portfolio_id` to identify the target entity.

        portfolio_id (str):
            Identifier of the portfolio-like entity this threshold applies to.

        side (str):
            Position side for which this threshold applies (long/short). Defined by `PortfolioSides`.

        threshold_type (str):
            Type of threshold rule (e.g., Profit Target, Stop Loss). Defined by `PortfolioThresholdTypes`.

        target_pct (Float):
            Percentage-based threshold applied for this rule. Required for all thresholds.

        target_value (Float):
            Absolute value-based threshold (e.g., exit when value increases by ₹10,000).
            Optional, cannot be set if `target_pct` is used.

        status (str):
            Current status of the threshold (e.g., Active, Inactive, Expired). Defined by `Status`.

        source (str):
            Origin of the threshold definition (User, Admin, Dealer). Defined by `ThresholdSource`.

        source_id (str):
            Identifier of the user/admin/dealer who defined this threshold.

        effective_from (datetime):
            Timestamp when this threshold became active. Automatically set at creation.

        effective_to (datetime | None):
            Optional timestamp when this threshold expires or is deactivated.

        triggered_at (datetime | None):
            Timestamp when this threshold was first hit/triggered. Useful for monitoring and audits.

        last_notification_sent_at (datetime | None):
            Timestamp of the most recent notification sent for this threshold hit.

        reason (str | None):
            Failure reason for the last attempted notification dispatch, if any.

        history (HistoricalRecords):
            Historical audit log for changes to this object.

    Notes:
        - Uses a polymorphic relation via `portfolio_type` and `portfolio_id`, so referential
          integrity to actual portfolio entities is not enforced at the database level.
        - `HistoricalRecords` will log all changes; consider pruning/archive strategies at scale.
    """

    class Meta:
        db_table = "user_portfolio_threshold"
        verbose_name = "User Portfolio Threshold"
        verbose_name_plural = "User Portfolio Thresholds"
        indexes = [
            models.Index(
                fields=["portfolio_type", "portfolio_id"],
                name="idx_portfolio_lookup"
            ),
            models.Index(
                fields=["portfolio_type", "portfolio_id", "side"],
                name="idx_portfolio_active_side",
                condition=Q(status=Status.ACTIVE)
            ),
            models.Index(
                fields=["portfolio_type", "portfolio_id", "threshold_type"],
                name="idx_portfolio_threshold_type"
            ),
        ]

    portfolio_type = models.CharField(
        max_length=50,
        blank=False,
        help_text="Entity type this threshold applies to (e.g., USER_PORTFOLIO, BASKET, STRATEGY)"
    )

    portfolio_id = models.CharField(
        max_length=100,
        blank=False,
        help_text="Entity ID this threshold applies to"
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
        help_text="Type of threshold rule"
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
    source_id = models.CharField(
        max_length=10,
        blank=False,
        help_text="Origin ID of the rule (User ID/Admin ID/Dealer ID)"
    )

    effective_from = models.DateTimeField(auto_now_add=True)
    effective_to = models.DateTimeField(null=True, blank=True)

    triggered_at = models.DateTimeField(null=True, blank=True)
    last_notification_sent_at = models.DateTimeField(null=True, blank=True)

    reason = models.TextField(null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return (
            f"{self.get_threshold_type_display()} Threshold "
            f"({self.portfolio_type}:{self.portfolio_id})"
        )

    @property
    def holdings_with_thresholds(self):
        """Return holdings and threshold metadata for this portfolio.

        For `USER_PORTFOLIO` thresholds, returns a dictionary with:
            {
                "holdings": {symbol: quantity, ...},
                "target_pct": self.target_pct,
                "target_value": self.target_value,
                "triggered_at": self.triggered_at,
                "last_notification_sent_at": self.last_notification_sent_at,
            }
        For other portfolio types, returns an empty dict.
        """
        # Local import to avoid circular dependencies at import time
        from apps.holdings.models.holdings import Holding
        from apps.portfolio.constants import USER_PORTFOLIO

        if self.portfolio_type != USER_PORTFOLIO:
            return {}

        holdings_qs = (
            Holding.objects
            .filter(user_portfolio=int(self.portfolio_id),
                    quantity__gte=0)
            .exclude(symbol='cash')
            .values_list("symbol", "quantity")
        )
        holdings_map = {symbol: quantity for symbol, quantity in holdings_qs}

        return {
            "holdings": holdings_map,
            "target_pct": self.target_pct,
            "target_value": self.target_value,
            "triggered_at": self.triggered_at,
            "last_notification_sent_at": self.last_notification_sent_at,
        }
