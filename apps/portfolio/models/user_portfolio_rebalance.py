"""
    User Portfolio Model
"""
import logging

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Sum
from django_extensions.db.models import TimeStampedModel

from apps.holdings.models import Transaction
from apps.portfolio.constants import (RebalanceTypes, States, CashTransaction, RebalanceTransactionTypes, Side,
                                      OrderStatus, RebalanceTransactionStates, Proxy)
from apps.portfolio.models import UserPortfolio
from apps.portfolio.constants import RebalanceStrategy

logger = logging.getLogger(__name__)


class UserPortfolioRebalance(TimeStampedModel):
    """
    Model to record user's portfolio rebalance data
    """
    class Meta:
        db_table = 'user_portfolio_rebalance'

    user_portfolio = models.ForeignKey(UserPortfolio, related_name="user_portfolio_rebalances",
                                       on_delete=models.CASCADE)
    type = models.CharField(choices=RebalanceTypes.CHOICES.value)
    states = ArrayField(models.CharField(max_length=20), null=False)
    current_state = models.CharField(max_length=20, default=States.PENDING.value, choices=States.CHOICES.value)
    rebalance_id = models.IntegerField(null=True, default=None)
    user_inputs = models.JSONField("UserInputs", null=False, default={})
    cash_ingested = models.FloatField(null=True)
    transaction_type = models.CharField(max_length=20, choices=CashTransaction.CHOICES.value)
    transaction = models.ForeignKey(Transaction, related_name="user_portfolio_rebalances", on_delete=models.CASCADE,
                                    null=True)
    metadata = models.JSONField("MetaData", null=False, default={})
    proxy = models.CharField(choices=Proxy.CHOICES.value, default=Proxy.USER.value)
    proxy_id = models.CharField(null=True, blank=True)
    instruction_url = models.URLField(default=None, null=True)
    rebalance_strategy = models.CharField(max_length=255, null=True, choices=RebalanceStrategy.choices())
    reason = models.TextField(null=True, default=None, blank=True)
    cash_carry_forward = models.FloatField(null=True, default=None, blank=True)

    def get_derived_values(self, types: list):
        """
        Add up the rebalance transaction buy and sell values
        :param types: initial, t0, t1
        :return:
        """
        # Use pythonic filtering and aggregation over related transactions.
        transactions = self.portfolio_rebalance_transactions.all()
        buy_value = sum(rt.buy_value for rt in transactions if rt.type in types)
        sell_value = sum(rt.sell_value for rt in transactions if rt.type in types)

        return {
            "buy_value": buy_value,
            "sell_value": sell_value
        }

    def rebalance_type(self):
        """
        Determine the rebalance type based on the current instance's attributes.

        Returns:
        str: The determined rebalance type, which can be one of the following values:
             - CashTransaction.WITHDRAW.value if the type is INITIAL and transaction_type is WITHDRAW.
             - RebalanceTypes.INVESTED.value if the type is INITIAL and transaction_type is ADD.
             - RebalanceTypes.REBALANCE.value if the type is REBALANCE and cash_ingested is 0.
             - RebalanceTypes.INVESTED_REBALANCE.value if the type is REBALANCE and cash_ingested is greater than 0.
             - RebalanceTypes.RECONCILIATION.value if the type is RECONCILIATION.
             - RebalanceTypes.CASH_ALLOCATION.value if the type is CASH_ALLOCATION.
        """
        if self.type == RebalanceTypes.INITIAL.value:
            if self.transaction_type == CashTransaction.WITHDRAW.value:
                return CashTransaction.WITHDRAW.value
            elif self.transaction_type == CashTransaction.ADD.value:
                return RebalanceTypes.INVESTED.value
        elif self.type == RebalanceTypes.REBALANCE.value:
            if not self.cash_ingested:
                return RebalanceTypes.REBALANCE.value
            elif self.cash_ingested:
                return RebalanceTypes.INVESTED_REBALANCE.value
        elif self.type == RebalanceTypes.RECONCILIATION.value:
            return RebalanceTypes.RECONCILIATION.value
        elif self.type == RebalanceTypes.CASH_ALLOCATION.value:
            return RebalanceTypes.CASH_ALLOCATION.value

    @property
    def buy_value(self):
        """
        Get the buy value from the derived values of all rebalance transactions.

        Returns:
        float: The buy value derived from all rebalance transactions.
        """
        return self.get_derived_values(RebalanceTransactionTypes.ALL.value).get("buy_value")

    @property
    def sell_value(self):
        """
        Get the sell value from the derived values of all rebalance transactions.

        Returns:
        float: The sell value derived from all rebalance transactions.
        """
        return self.get_derived_values(RebalanceTransactionTypes.ALL.value).get("sell_value")

    @property
    def initial_transaction_value(self):
        """
        Returns the summations of all the initial userportfolio rebalance transactions of one userportfolio rebalance
        :return:
        """
        return self.portfolio_rebalance_transactions.filter(type=RebalanceTransactionTypes.INITIAL.value). \
            aggregate(total=Sum("amount"))['total']

    @property
    def t0_transaction_value(self):
        """
        Returns the summations of all the t0 userportfolio rebalance transactions of one userportfolio rebalance
        :return:
        """
        return self.portfolio_rebalance_transactions.filter(type=RebalanceTransactionTypes.T0.value). \
            aggregate(total=Sum("amount"))['total']

    @property
    def t1_transaction_value(self):
        """
        Returns the summations of all the t1 userportfolio rebalance transactions of one userportfolio rebalance
        :return:
        """
        return self.portfolio_rebalance_transactions.filter(type=RebalanceTransactionTypes.T1.value). \
            aggregate(total=Sum("amount"))['total']
    @property
    def cash_allocation_transaction_value(self):
        """
        Returns the summations of all the cash_allocation userportfolio rebalance transactions of one userportfolio rebalance
        :return:
        """
        return self.portfolio_rebalance_transactions.filter(type=RebalanceTransactionTypes.CASH_ALLOCATION.value). \
            aggregate(total=Sum("amount"))['total']

    @property
    def initial_remaining_value(self):
        """
        Returns the remaining value of an initial rebalance
        :return:
        """
        derived_values = self.get_derived_values([RebalanceTransactionTypes.INITIAL.value])
        buy_value = abs(derived_values.get("buy_value"))
        buffer_amount = self.user_inputs.get("buffer_amount", 0)
        if buy_value and self.cash_ingested:
            return abs(self.cash_value - buy_value - buffer_amount)
        return buy_value

    @property
    def t0_remaining_value(self):
        """
        Returns the remaining value of a t0 rebalance
        :return:
        """
        derived_values = self.get_derived_values([RebalanceTransactionTypes.T0.value])
        buy_value = derived_values.get("buy_value")
        sell_value = derived_values.get("sell_value")
        buffer_amount = self.user_inputs.get("buffer_amount", 0)
        cash_buffer_amount = self.user_inputs.get("cash_buffer_amount", 0)
        if self.cash_ingested:
            cash_ingested = float(self.cash_ingested) -float(cash_buffer_amount)
            return (sell_value + cash_ingested) - buy_value - buffer_amount
        return sell_value - buy_value - buffer_amount

    @property
    def t1_remaining_value(self):
        """
        Returns the remaining value of a t1 rebalance
        :return:
        """
        logger.info("In t1_remaining_value")
        derived_values = self.get_derived_values([RebalanceTransactionTypes.T1.value, RebalanceTransactionTypes.T0.value])
        buffer_amount = self.user_inputs.get("buffer_amount", 0)
        cash_buffer_amount = self.user_inputs.get("cash_buffer_amount", 0)
        if (abs(derived_values.get("buy_value")) or abs(derived_values.get("sell_value"))) and self.cash_ingested:
            return abs((derived_values['sell_value'] + self.cash_value) - derived_values['buy_value'] - buffer_amount - cash_buffer_amount)
        return abs(derived_values['sell_value'] - derived_values['buy_value'] - buffer_amount)

    @property
    def cash_allocation_remaining_value(self):
        """
        Returns the remaining value of a cash_allocation rebalance
        :return:
        """
        derived_values = self.get_derived_values([RebalanceTransactionTypes.CASH_ALLOCATION.value])
        buy_value = abs(derived_values.get("buy_value"))
        sell_value = abs(derived_values.get("sell_value"))
        buffer_amount = self.user_inputs.get("buffer_amount", 0)
        if self.cash_ingested:
            return (sell_value + self.cash_ingested) - buy_value
        return sell_value - buy_value - buffer_amount

    @property
    def total_invested_value(self):
        """
        Returns the remaining value of a t1 rebalance
        :return:
        """
        # Use pythonic filtering similar to other derived computations.
        relevant_types = [
            RebalanceTransactionTypes.T0.value,
            RebalanceTransactionTypes.T1.value,
            RebalanceTransactionTypes.INITIAL.value,
            RebalanceTransactionTypes.CASH_ALLOCATION.value,
        ]

        derived_values = self.get_derived_values(relevant_types)

        # Select the earliest matching transaction in-memory (by id), if any.
        transactions = [rt for rt in self.portfolio_rebalance_transactions.all() if rt.type in relevant_types]
        earliest_txn = min(transactions, key=lambda rt: rt.id) if transactions else None

        # Safely read retained_position_value from user_rebalance_json when present and dict-like.
        retained_tickers_value = 0
        if earliest_txn and getattr(earliest_txn, 'user_rebalance_json', None):
            try:
                retained_tickers_value = earliest_txn.user_rebalance_json.get('retained_position_value', 0)
            except AttributeError:
                # If user_rebalance_json isn't a dict
                retained_tickers_value = 0

        return derived_values.get('buy_value', 0) + (retained_tickers_value or 0)

    @property
    def is_sell_completed(self):
        """
        Checks all the sell user instructions if executed or not
        :return: Boolean
        """
        from apps.portfolio.services.user_portfolio_rebalance import get_latest_user_instructions_of_rebalance
        logger.info(f"In is_sell_completed")
        user_instruction_list = get_latest_user_instructions_of_rebalance(self.id, RebalanceTransactionTypes.ALL.value)
        for user_instruction in user_instruction_list:
            if (user_instruction.get('side') == Side.SELL.value and
                    user_instruction.get('status') != OrderStatus.FILLED.value):
                return False
        return True

    @property
    def get_phase_details_of_rebalance(self):
        """
        Responds with phase details of a rebalance.
        eg. if the sell phase is completed or not and if completed what's pending in buy
        :return:
        """
        from apps.portfolio.services.user_portfolio_rebalance import get_user_instructions
        logger.info(f"In get_phase_details_of_rebalance {self.id = }")
        derived_values = self.get_derived_values(
            [RebalanceTransactionTypes.T0.value, RebalanceTransactionTypes.T1.value,
             RebalanceTransactionTypes.INITIAL.value])
        phase_details = {
            "user_portfolio_rebalance_id": self.id,
            "metadata": self.metadata,
            "product_type": self.user_portfolio.product_type,
            "sell_phase": {
                "sell_value": derived_values.get("sell_value"),
                "transaction_type": self.transaction_type,
            },
            "buy_phase": {
                "buy_user_instructions": get_user_instructions(self.id, Side.BUY.value,
                                                               OrderStatus.WAITING.value,
                                                               [RebalanceTransactionStates.RETRY_ENABLED.value])
            }
        }
        logger.info(f"{phase_details = }")
        return phase_details

    @property
    def cash_value(self):
        if self.transaction_type == CashTransaction.WITHDRAW.value:
            return -1 * abs(self.cash_ingested)
        else:
            return self.cash_ingested
