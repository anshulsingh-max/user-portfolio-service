import logging

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Sum
from django_extensions.db.models import TimeStampedModel
from apps.portfolio.constants import OrderCurrentStatus, Side
from apps.portfolio.models.mixins import TimestampStrMixin

logger = logging.getLogger(__name__)


class Order(TimestampStrMixin, TimeStampedModel):
    """
    A model representing a financial order placed within a user's basket.

    Attributes:
        basket (Basket): ForeignKey to the Basket model, representing the basket
            this order belongs to.
        trading_symbol (str): The trading symbol for the financial instrument being traded.
        buy_price (float, optional): The price at which the order was bought. Can be null.
        sell_price (float, optional): The price at which the order was sold. Can be null.
         current_status (str): The current status of the order, defaulting to 'WAITING'.
            This field uses predefined order states from the OrderCurrentStatues enum.
        states (list): An array field storing a history of states that the order has passed through.
        initial_amount (float, optional): The amount of the order after being bought. Can be null.
        end_amount (float, optional): The amount of the order after being sold. Can be null.
        stop_loss (float, optional): The stop-loss value associated with the order.
        leverage (float): The leverage applied to the order.

    Meta:
        db_table (str): The name of the database table for this model ('orders').
    """

    class Meta:
        db_table = 'orders'

    basket = models.ForeignKey('portfolio.Basket', related_name="user_basket", on_delete=models.CASCADE)
    trading_symbol = models.CharField(max_length=100)
    buy_price = models.FloatField(null=True)
    sell_price = models.FloatField(null=True, blank=True)
    current_status = models.CharField(max_length=20,
                                      default=OrderCurrentStatus.WAITING.value,
                                      choices=OrderCurrentStatus.CHOICES.value)
    states = ArrayField(models.CharField(max_length=20), null=False, default=list)
    initial_amount = models.FloatField(null=True)
    end_amount = models.FloatField(null=True, blank=True)
    stop_loss = models.FloatField(null=True)
    leverage = models.FloatField()
    stop_loss_hit = models.BooleanField(null=True, blank=True)
    stop_loss_hit_time = models.DateTimeField(null=True, blank=True)
    last_notification_sent = models.DateTimeField(null=True, blank=True)

    def __get_filled_quantity(self, side):
        return (
            self.user_order.filter(side=side)
            .aggregate(total=Sum("filled_quantity"))
            .get("total")
        )

    @property
    def buy_quantity(self) -> float:
        """Total quantity across all BUY-side instructions for this order."""
        logger.info("In buy_quantity")
        total = self.__get_filled_quantity(Side.BUY.value)
        logger.info(f'{total = }')
        return total or 0.0

    @property
    def sell_quantity(self) -> float:
        """Total quantity across all SELL-side instructions for this order."""
        logger.info("In sell_quantity")
        total = self.__get_filled_quantity(Side.SELL.value)
        logger.info(f'{total = }')
        return total or 0.0
