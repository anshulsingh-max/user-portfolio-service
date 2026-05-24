"""
    User Portfolio Model
"""
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.aggregates import Sum
from django_extensions.db.models import TimeStampedModel

from apps.portfolio.constants import RebalanceTransactionTypes, RebalanceTransactionStates, Side, OrderStatus
from apps.portfolio.models import UserPortfolioRebalance


class PortfolioRebalanceTransaction(TimeStampedModel):
    """
    Model to represent Portfolio Rebalance transaction
    """

    class Meta:
        db_table = 'portfolio_rebalance_transaction'

    portfolio_rebalance = models.ForeignKey(UserPortfolioRebalance, related_name="portfolio_rebalance_transactions",
                                            on_delete=models.CASCADE)
    allocation_quantity = models.JSONField(verbose_name="UserAllocationQuantity", default={})
    user_rebalance_json = models.JSONField(verbose_name="UserRebalanceJson", default={})
    type = models.CharField(max_length=20, choices=RebalanceTransactionTypes.CHOICES.value,
                            default=RebalanceTransactionTypes.INITIAL.value)
    current_state = models.CharField(max_length=50, choices=RebalanceTransactionStates.CHOICES.value,
                                     default=RebalanceTransactionStates.PROCESSING.value)
    executed_list = ArrayField(models.CharField(max_length=20), null=True)
    amount = models.FloatField(validators=[MinValueValidator(0.0)], default=0)
    instruction_url = models.URLField(default=None, null=True)

    @property
    def buy_value(self):
        """
        Sum of all the bought value of user instructions in a rebalanc243e transaction
        :return:
        """
        # If there are no user_instructions, sum on an empty iterable returns 0.
        # Also coalesce None values to 0 to avoid TypeError when summing.
        return sum(
            (instruction.value or 0) for instruction in self.user_instructions.all()
            if instruction.side == Side.BUY.value and instruction.status == OrderStatus.FILLED.value
        )

    @property
    def sell_value(self):
        """
        Sum of all the sold value of user instructions in a rebalance transaction
        :return:
        """
        # If there are no user_instructions, sum on an empty iterable returns 0.
        # Also coalesce None values to 0 to avoid TypeError when summing.
        return sum(
            (instruction.value or 0) for instruction in self.user_instructions.all()
            if instruction.side == Side.SELL.value and instruction.status == OrderStatus.FILLED.value
        )
