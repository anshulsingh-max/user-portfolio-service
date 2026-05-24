"""
basket.py

The Basket model is used within the portfolio management system to organize and
monitor a user's investments and trading activities.
"""

from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.db.models import Sum

from apps.portfolio.constants import (
    BasketStates,
    BasketTypes,
    ProductTypes,
    BrokerEnum,
    OrderCurrentStatus,
)


class Basket(TimeStampedModel):
    """
    A model representing a user's basket of financial instruments or trades.

    Attributes:
        user_id (str): The unique identifier for the user who owns the basket.
        current_state (str): The current state of the basket, represented as
            a choice from predefined states. Defaults to 'WAITING'.
        model_id (str): The identifier for the associated model (e.g., trading model).
        payment_id (str): The identifier for the payment associated with the basket.
        recommendation_id (int): The identifier for the recommendation associated with
            the basket.
        user_allocation (dict): A JSON field storing user allocation data.
        cash_ingested (float, optional): The amount of cash ingested into the basket.
        amount (float, optional): The total amount associated with the basket.
        profit_target (float, optional): The target profit for the basket.
        profit_target_value (float, optional): The value of the target profit.
        basket_type (str, optional): The type of basket, selected from predefined choices.
        product_type (str, optional): The type of product associated with the basket, selected from predefined choices.
        end_amount (str, float): Amount after the stocks are sold.

    Meta:
        db_table (str): The name of the database table for this model.
    """

    class Meta:
        db_table = 'basket'

    user_id = models.CharField(max_length=100, null=False)
    current_state = models.CharField(max_length=20,
                                     default=BasketStates.UNINVESTED.value,
                                     choices=BasketStates.CHOICES.value)
    broker = models.CharField(choices=BrokerEnum.CHOICES.value, null=True, blank=True)
    model_id = models.CharField()
    payment_id = models.CharField()
    recommendation_id = models.IntegerField()
    user_allocation = models.JSONField(default=dict)
    cash_ingested = models.FloatField(null=True)
    amount = models.FloatField(null=True)
    profit_target_1 = models.FloatField(null=True, blank=True)
    profit_target_1_value = models.FloatField(null=True, blank=True)
    profit_target_2 = models.FloatField(null=True, blank=True)
    profit_target_2_value = models.FloatField(null=True, blank=True)
    basket_type = models.CharField(choices=BasketTypes.CHOICES.value, null=True)
    product_type = models.CharField(choices=ProductTypes.CHOICES.value, null=True)
    end_amount = models.CharField(default=0.0)
    pt1_hit = models.BooleanField(null=True, blank=True)
    pt2_hit = models.BooleanField(null=True, blank=True)
    pt1_hit_time = models.DateTimeField(null=True, blank=True)
    pt2_hit_time = models.DateTimeField(null=True, blank=True)
    last_notification_sent = models.DateTimeField(null=True, blank=True)

    @property
    def created_str(self) -> str:
        """
        Returns an ISO 8601 string representation of the created datetime.
        Format: 'YYYY-MM-DDTHH:MM:SSZ'
        """
        return self.created.isoformat() if self.created else ""

    @property
    def modified_str(self) -> str:
        """
        Returns an ISO 8601 string representation of the modified datetime.
        Format: 'YYYY-MM-DDTHH:MM:SSZ'
        """
        return self.modified.isoformat() if self.modified else ""

    @property
    def exposure_amount(self) -> float:
        """Return the capital that is still deployed in the market for this basket.

        New logic:
            * For every `Order` in this basket aggregate the executed quantities
              from its related `OrderInstruction` objects.
            * Net Quantity  = ``total_buy_quantity - total_sell_quantity``.
              If this figure is **<= 0** we no longer carry any open position
              for that security/order.
            * Exposure per order/security is therefore
              ``net_quantity * order.buy_price`` where ``order.buy_price`` is
              assumed to be the average execution price of the original BUY.
            * The basket's ``exposure_amount`` is the sum of exposure across
              all its constituent orders.
        """

        total_exposure = 0.0

        # Iterate over all orders in this basket.  The related_name ``user_basket``
        # is defined on the ``Order`` model -> ``basket`` ForeignKey.
        for order in self.user_basket.all():
            # Quantities are already aggregated per side on the ``Order`` model
            # via the ``buy_quantity`` and ``sell_quantity`` properties.
            net_quantity = (order.buy_quantity or 0.0) - (order.sell_quantity or 0.0)

            # Only positive net quantities represent an open / partially open
            # position.  Zero or negative implies the position has been fully
            # squared-off or net-short which we do not count towards exposure.
            if net_quantity > 0 and order.buy_price:
                total_exposure += net_quantity * order.buy_price

        return total_exposure
