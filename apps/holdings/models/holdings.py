from django.core.validators import MinValueValidator
from django.db import models
from django_extensions.db.models import TimeStampedModel

from apps.holdings.constants import TransactionStates, TransactionParticipants


class Holding(TimeStampedModel):
    """
        Model to record holdings of a specific user portfolio
    """
    from apps.portfolio.models import UserPortfolio

    class Meta:
        db_table = 'holding'

    constraints = [
        models.UniqueConstraint(fields=['user_portfolio', 'symbol'], name='user_portfolio_symbol_unique_value')
    ]

    user_portfolio = models.ForeignKey(UserPortfolio, related_name="holdings", on_delete=models.CASCADE)
    symbol = models.CharField(max_length=30)
    quantity = models.FloatField(validators=[MinValueValidator(0.0)])
    avg_buy_price = models.FloatField(default=0)

    @property
    def portfolio_id(self):
        return self.user_portfolio.portfolio_id
