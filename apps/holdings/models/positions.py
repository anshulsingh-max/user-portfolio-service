"""
Models for the positions in Holdings app.

This module defines the `Position` model, which tracks holdings for a
specific user portfolio, ensuring that each combination of basket and
symbol is unique.
"""

from django.core.validators import MinValueValidator
from django.db import models
from django_extensions.db.models import TimeStampedModel


class Position(TimeStampedModel):
    """
    Model to record holdings of a specific user portfolio.

    The `Position` model represents an individual holding in a user's
    portfolio, where each position corresponds to a particular `symbol` (e.g.,
    stock, asset) held within a `basket`. Each `basket` can hold multiple
    symbols, and the model ensures that no duplicate entries exist for the
    same basket-symbol combination.

    Attributes:
        basket (ForeignKey): The user's investment basket that holds the position.
        symbol (CharField): The symbol representing the asset (e.g., stock ticker).
        quantity (FloatField): The amount of the asset held, which must be non-negative.
        buy_price (FloatField): The price at which the security was bought.
    """

    class Meta:
        db_table = 'position'
        constraints = [
            models.UniqueConstraint(fields=['basket', 'symbol'], name='basket_symbol_unique_value')
        ]

    basket = models.ForeignKey(
        'portfolio.Basket',
        related_name="positions",
        on_delete=models.CASCADE
    )
    symbol = models.CharField(max_length=30)
    quantity = models.FloatField(validators=[MinValueValidator(0.0)])
    buy_price = models.FloatField(default=0)
