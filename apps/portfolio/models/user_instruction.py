"""
    User Portfolio Model
"""
from django.db import models
from django_extensions.db.models import TimeStampedModel

from apps.portfolio.constants import (Side, OrderStatus)
from apps.portfolio.models import UserPortfolioRebalance, PortfolioRebalanceTransaction


class UserInstruction(TimeStampedModel):
    """
    Model to record user instructions for trade execution
    """
    class Meta:
        db_table = 'user_instruction'

    portfolio_rebalance_transaction = models.ForeignKey(PortfolioRebalanceTransaction, related_name="user_instructions",
                                                 on_delete=models.CASCADE)
    trade_placement_id = models.IntegerField(null=True, unique=True)
    # order_tag uniqueness: UNIQUE on UserInstruction (Flow A / rebalance),
    # contrast OrderInstruction.order_tag which is NOT unique (Flow B / basket).
    # Open decision §13.3.2 of the unification plan — align before Phase 2.
    order_tag = models.CharField(null=False, max_length=50, unique=True)
    symbol = models.CharField(max_length=30, null=False)
    quantity = models.FloatField()
    filled_quantity = models.FloatField(default=0)
    side = models.CharField(max_length=20, choices=Side.CHOICES.value)
    leverage = models.FloatField(null=True, blank=True)
    price = models.FloatField(null=True)
    value = models.FloatField(null=True)
    status = models.CharField(max_length=20, default=OrderStatus.WAITING.value, choices=OrderStatus.CHOICES.value)
    reason = models.TextField(null=True, blank=True, default="")
    asm_consent = models.BooleanField(null=True)
    asm_reason = models.TextField(null=True, blank=True)
    retry_allowed = models.BooleanField(default=True)
