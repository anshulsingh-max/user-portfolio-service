"""
    Signals of holdings app
"""
import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.holdings.constants import TransactionParticipants
from apps.holdings.models import Transaction, Position
from apps.holdings.services.transaction import update_or_create_holding
from apps.portfolio.constants import Asset, Side
from apps.portfolio.models import OrderInstruction


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def holdings_transaction_save(sender, instance, created, **kwargs):
    """
        Post save signal for Holdings Transaction
     """
    logger.info("Holdings Transaction save signal")
    logger.info(f"Current status {instance.id} is {instance.current_state}")

    amount = instance.amount
    if instance.source == TransactionParticipants.PORTFOLIO.value:
        amount = instance.amount * -1

    if created:
        update_or_create_holding(instance.user_portfolio, Asset.CASH.value, amount, Asset.CASH_PRICE.value)


@receiver(post_save, sender=OrderInstruction)
def order_instruction_save(sender, instance, created, **kwargs):
    """
    Signal handler to update positions after an OrderInstruction is saved.
    """
    logger.info(f"OrderInstruction ID: {instance.id}, Status: {instance.status}, Side: {instance.side}")

    try:
        with transaction.atomic():
            buy_price = instance.order_price if instance.side == Side.BUY.value else None
            position_instance, position_created = Position.objects.get_or_create(
                basket=instance.order.basket,
                symbol=instance.symbol,
                defaults={'quantity': 0}
            )

            quantity_change = instance.filled_quantity * (1 if instance.side == Side.BUY.value else -1)
            if quantity_change != 0:
                position_instance.quantity += quantity_change
                if instance.side == Side.BUY.value and buy_price is not None:
                    position_instance.buy_price = buy_price
                position_instance.save()

                if position_created:
                    logger.info(f"Position created: basket = {position_instance.basket}, symbol = {position_instance.symbol}, quantity = {position_instance.quantity}")
                else:
                    logger.info(f"Position updated: basket = {position_instance.basket}, symbol = {position_instance.symbol}, quantity = {position_instance.quantity}")
            else:
                logger.info("No change in position quantity, skipping save.")
    except Exception as exc:
        logger.error(f"Error while updating/creating position: {exc}")
        logger.exception(exc)
        raise exc
