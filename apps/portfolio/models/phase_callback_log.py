from django.db import models
from django_extensions.db.models import TimeStampedModel

from apps.portfolio.constants import PhaseCallbackLogEnum
from apps.portfolio.models import PortfolioRebalanceTransaction


class PhaseCallbackLog(TimeStampedModel):
    """
    Model to phase callback log, it logs all the communication going to the rebalancing business service for
    processing buy orders post sell in case of rebalance
    """
    class Meta:
        db_table = 'phase_callback_log'

    user_id = models.CharField(max_length=100, null=False)
    portfolio_rebalance_transaction = models.ForeignKey(PortfolioRebalanceTransaction, related_name="phase_callback",
                                                        on_delete=models.CASCADE)
    phase_id = models.CharField(max_length=100, null=False, unique=True)
    status = models.CharField(max_length=20, default=PhaseCallbackLogEnum.PROCESSING.value,
                              choices=PhaseCallbackLogEnum.CHOICES.value)
    reason = models.TextField(null=True, blank=True)