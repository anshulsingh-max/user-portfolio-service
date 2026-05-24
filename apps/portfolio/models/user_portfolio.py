"""
    User Portfolio Model
"""
import logging
from datetime import datetime

from django.db import models
from django.db.models import F, FloatField, UniqueConstraint
from django.db.models.aggregates import Sum
from django_extensions.db.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from apps.portfolio.constants import (UserPortfolioStatus, Asset, BrokerEnum, Proxy, ProductTypes, Strategy)

logger = logging.getLogger(__name__)

class UserPortfolio(TimeStampedModel):
    """
    Model to user's portfolio data
    """
    class Meta:
        db_table = 'user_portfolio'
        constraints = [
            UniqueConstraint(
                fields=['user_id', 'subscription_id', 'portfolio_id', 'status'],
                name='unique_user_subscription',
            ),
        ]

    user_id = models.CharField(max_length=100, null=False)
    name = models.CharField(max_length=100, null=False)
    portfolio_id = models.CharField(max_length=100, null=False)
    status = models.CharField(choices=UserPortfolioStatus.CHOICES.value, default=UserPortfolioStatus.ACTIVE.value)
    subscription_id = models.CharField(max_length=100)
    broker = models.CharField(max_length=50, null=False, default=BrokerEnum.PAPER_TRADE.value)
    deactivated_reason = models.TextField(null=True, blank=True)
    proxy = models.CharField(choices=Proxy.CHOICES.value, default=Proxy.USER.value)
    proxy_id = models.CharField(null=True, blank=True)
    history = HistoricalRecords()
    expected_investment = models.FloatField(null=True, blank=True)
    product_type = models.CharField(choices=ProductTypes.CHOICES.value,
                                    null=True, blank=True,
                                    default=ProductTypes.EQUITY.value)
    strategy = models.CharField(choices=Strategy.CHOICES.value,
                                null=True, blank=True,
                                default=Strategy.REBALANCE.value)

    @property
    def remaining_amount(self):
        mainquantity=0
        for holds in self.holdings.all():
            if holds.symbol == Asset.CASH.value:
                mainquantity = holds.quantity
        return mainquantity

    @property
    def invested_amount(self):
        mainsum=0
        for holds in self.holdings.all():
            if holds.symbol != Asset.CASH.value:
                mainsum += holds.quantity * holds.avg_buy_price
        return mainsum

    @property
    def mtf_invested_amount(self):
        """
        Calculate invested amount for MTF portfolios based on strategy.

        * For `Strategy.REBALANCE` – returns current invested amount from holdings
          (sum of quantity * avg_buy_price for non-cash symbols).
        * For `Strategy.ONE_TIME` – uses the value of BUY-side `UserInstruction`s
          from the first `UserPortfolioRebalance`.
        * For non-MTF product types – returns 0.
        """
        if self.product_type != ProductTypes.MTF.value:
            return 0

        # Use prefetched holdings to avoid additional queries
        total = sum(
            holding.quantity * holding.avg_buy_price
            for holding in self.holdings.all()
            if holding.symbol != Asset.CASH.value
        )
        return total or 0


    @property
    def average_leverage(self):
        """Return weighted average leverage for all filled BUY instructions.

        Formula::
            sum(leverage_i * value_i) / sum(value_i)

        If the portfolio has no qualifying instructions, ``None`` is returned.
        """
        if self.product_type != ProductTypes.MTF.value:
            return 0
        from apps.portfolio.constants import Side, OrderStatus

        # Use prefetched data to avoid additional queries
        total_weighted = 0
        total_value = 0

        for rebalance in self.user_portfolio_rebalances.all():
            for transaction in rebalance.portfolio_rebalance_transactions.all():
                for instruction in transaction.user_instructions.all():
                    if (instruction.side == Side.BUY.value and
                        instruction.status == OrderStatus.FILLED.value and
                        instruction.leverage is not None and
                        instruction.value is not None):
                        total_weighted += instruction.leverage * instruction.value
                        total_value += instruction.value

        if not total_value:
            return 0

        return round(total_weighted / total_value, 2)

    @property
    def investment_date(self):
        """Return the created timestamp of the first related UserPortfolioRebalance.

        If no rebalance exists, returns None.
        """
        # Use prefetched data to avoid additional queries

        rebalances = list(self.user_portfolio_rebalances.all())
        if rebalances:
            first_rebalance = min(rebalances, key=lambda r: r.id)
            return first_rebalance.created
        return None

    @property
    def total_cash_ingested(self) -> float:
        """
        Calculate the total invested amount from a list of rebalance and allocation transactions.

        The function processes transactions in chronological order:
        - If an 'initial' ADD transaction is found, its rebalance values are included.
          If followed by a 'cash_allocation' transaction, that value is also added.
        - For 'rebalance' ADD transactions, the 'cash_ingested' field is added.

        :param transactions: List of portfolio transaction dictionaries.
        :return: Total invested amount as a float.
        """
        from apps.portfolio.services.rebalance_transaction import extract_invested_value

        transactions = [
            t for r in self.user_portfolio_rebalances.all()
            for t in r.portfolio_rebalance_transactions.all()
        ]
        if not transactions:
            logger.info("No transactions provided. Returning 0.0.")
            return 0.0

        logger.info("Starting calculation of invested amount. Transactions received: %d", len(transactions))
        try:
            sorted_transactions = sorted(
                transactions,
                key=lambda tx: tx.created
            )
        except Exception as e:
            logger.exception("Failed to sort transactions by created timestamp: %s", e)
            return 0.0

        total_invested = 0.0

        for i, tx in enumerate(sorted_transactions):
            tx_type = tx.type
            tx_action = tx.portfolio_rebalance.transaction_type
            logger.debug("Processing transaction %d/%d: %s", i + 1, len(sorted_transactions), tx)

            # Initial investment
            if tx_type == "initial" and tx_action == "add":
                invested = extract_invested_value(tx)
                total_invested += invested
                logger.info("Initial investment detected. Value: %.2f", invested)

                if i + 1 < len(sorted_transactions) and sorted_transactions[i + 1].type == "cash_allocation":
                    allocation_tx = sorted_transactions[i + 1]
                    allocation_value = extract_invested_value(allocation_tx)
                    total_invested += allocation_value
                    logger.info("Cash allocation added. Value: %.2f, Running Total: %.2f", allocation_value,
                                total_invested)

            # Rebalance additions
            elif tx_type == "rebalance" and tx_action == "add":
                cash_ingested = tx.cash_ingested if tx.cash_ingested else 0
                total_invested += max(extract_invested_value(tx), 0)
                logger.info("Rebalance cash ingested. Value: %.2f, Running Total: %.2f", cash_ingested, total_invested)

                if i + 1 < len(sorted_transactions) and sorted_transactions[i + 1].type == "cash_allocation":
                    allocation_tx = sorted_transactions[i + 1]
                    allocation_value = extract_invested_value(allocation_tx)
                    total_invested += allocation_value
                    logger.info("Cash allocation added. Value: %.2f, Running Total: %.2f", allocation_value,
                                total_invested)

        logger.info("Final total invested amount: %.2f", total_invested)
        return total_invested