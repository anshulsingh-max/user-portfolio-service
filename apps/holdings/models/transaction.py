from django.core.validators import MinValueValidator
from django.db import models
from django_extensions.db.models import TimeStampedModel

from apps.holdings.constants import TransactionStates, TransactionParticipants, TransactionTypes


class Transaction(TimeStampedModel):
    """
    Model to record transaction
    """
    from apps.portfolio.models import UserPortfolio

    class Meta:
        db_table = 'transaction'

    user_portfolio = models.ForeignKey(UserPortfolio, related_name="transactions", on_delete=models.CASCADE)
    source = models.CharField(max_length=20, choices=TransactionParticipants.CHOICES.value)
    target = models.CharField(max_length=20, choices=TransactionParticipants.CHOICES.value)
    amount = models.FloatField(validators=[MinValueValidator(0.0)])
    type = models.CharField(max_length=20, choices=TransactionTypes.CHOICES.value)
    current_state = models.CharField(max_length=20, choices=TransactionStates.CHOICES.value,
                                     default=TransactionStates.COMPLETE.value)
