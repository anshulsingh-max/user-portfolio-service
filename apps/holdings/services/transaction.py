"""
    Transaction services module
"""
import logging

from apps.holdings.constants import TransactionParticipants, TransactionTypes, TransactionStates
from apps.holdings.models import Holding, Transaction
from apps.portfolio.constants import RebalanceTypes

logger = logging.getLogger(__name__)


def update_or_create_holding(user_portfolio_id, symbol, quantity, buy_price=0):
    """
        This function if not present holding and user portfolio id combination than creates it else updates.
        Updating logic is to add the amount to whatever present (sign of amount can vary as + and -)
        :param buy_price: buying price of the asset(symbol or cache)
        :param user_portfolio_id: User portfolio which it belongs to
        :param symbol: Symbol of ASSET
        :param quantity: Quantity of asset
        :return:
    """
    logger.info(f"In create_or_update_holdings {user_portfolio_id = }, {symbol = }, {quantity = }, {buy_price = }")
    try:
        # https://bridgeweave-sq.sentry.io/issues/6545599736/?environment=prod&project=4506156424953856&query=is%3Aunresolved&referrer=issue-stream
        # Use get_or_create for atomic operation - prevents race conditions
        holding_obj, created = Holding.objects.get_or_create(
            user_portfolio=user_portfolio_id,
            symbol=symbol,
            defaults={'quantity': quantity, 'avg_buy_price': buy_price}
        )

        if created:
            logger.info(f"Created new holding object {holding_obj.id=} with {quantity=}")
        else:
            # Update existing holding
            logger.info(f"Updating existing holding object {holding_obj.id=} {holding_obj.quantity=}")

            # Calculate new average buy price when adding quantity
            if quantity > 0:
                holding_obj.avg_buy_price = (
                    (holding_obj.avg_buy_price * holding_obj.quantity + quantity * buy_price) /
                    (holding_obj.quantity + quantity)
                ) if buy_price else buy_price

            holding_obj.quantity += quantity
            logger.info(f"New quantity {holding_obj.quantity=}")
            holding_obj.save()
    except Exception as e:
        logger.exception(e)



def revert_cash_transaction(data_obj):
    if data_obj.amount == 0 and data_obj.type == RebalanceTypes.INITIAL.value:
        user_portfolio_obj = data_obj.portfolio_rebalance.user_portfolio
        Transaction.objects.create(**{
            "user_portfolio": user_portfolio_obj,
            "source": TransactionParticipants.PORTFOLIO.value,
            "target": TransactionParticipants.USER.value,
            "amount": data_obj.portfolio_rebalance.cash_ingested,
            "type": TransactionTypes.UNINVESTED.value,
            "current_state": TransactionStates.COMPLETE.value
        })
