from django.db import models
from django_extensions.db.models import TimeStampedModel
from apps.portfolio.constants import Side, OrderStatus, OrderInstructionSources
from apps.portfolio.models import Order


class OrderInstruction(TimeStampedModel):
    """
    A model representing detailed instructions for an individual order.

    Attributes:
        order (Order): ForeignKey to the `Order` model, representing the order this instruction is associated with.
        trade_placement_id (int, optional): A unique identifier for the trade placement.
        order_tag (str): A unique tag or identifier for this specific instruction.
        symbol (str): The trading symbol for the financial instrument involved in the order.
        quantity (float): The total quantity involved in the instruction.
        filled_quantity (float, default=0): The quantity that has been filled (executed).
        order_price Optional(float): The price at which the order was placed.
        side (str): The side of the order (buy/sell), chosen from predefined sides.
        value (float, optional): The monetary value of the instruction.
        status (str): The current status of the instruction, defaulting to 'WAITING'.
            The status is chosen from predefined order statuses.
        reason (str, optional): A text field to provide a reason or additional information related to the instruction.
        source (str): The source of instruction, defaulting to 'normal'.

    Meta:
        db_table (str): The name of the database table for this model ('order_instruction').
    """

    class Meta:
        db_table = 'order_instruction'

    order = models.ForeignKey(Order, related_name="user_order", on_delete=models.CASCADE)
    trade_placement_id = models.IntegerField(null=True, unique=True)
    order_tag = models.CharField(null=False, max_length=50)
    symbol = models.CharField(max_length=30, null=False)
    quantity = models.FloatField()
    filled_quantity = models.FloatField(default=0)
    order_price = models.FloatField(null=True)
    side = models.CharField(max_length=20, choices=Side.CHOICES.value)
    source = models.CharField(max_length=20,
                              choices=OrderInstructionSources.CHOICES.value,
                              default=OrderInstructionSources.MANUAL.value)
    value = models.FloatField(null=True)
    status = models.CharField(max_length=20, default=OrderStatus.WAITING.value, choices=OrderStatus.CHOICES.value)
    reason = models.TextField(null=True, blank=True, default="")

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
