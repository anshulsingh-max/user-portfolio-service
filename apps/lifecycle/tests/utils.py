"""Shared factories for lifecycle foundation tests.

The factories disconnect legacy post-save signals so these tests exercise only
the new lifecycle authority instead of existing business side effects.
"""

from __future__ import annotations

from django.db.models.signals import post_save

from apps.portfolio import signals
from apps.portfolio.constants import (
    BasketStates,
    BasketTypes,
    BrokerEnum,
    CashTransaction,
    OrderCurrentStatus,
    ProductTypes,
    RebalanceTransactionStates,
    RebalanceTransactionTypes,
    RebalanceTypes,
    States,
)
from apps.portfolio.models import (
    Basket,
    Order,
    OrderInstruction,
    PortfolioRebalanceTransaction,
    UserInstruction,
    UserPortfolio,
    UserPortfolioRebalance,
)

SIGNAL_RECEIVERS = [
    (signals.rebalance_transaction_save, PortfolioRebalanceTransaction),
    (signals.user_instructions_save, UserInstruction),
    (signals.user_basket_save, Basket),
    (signals.orders_save, Order),
    (signals.order_instruction_save, OrderInstruction),
    (signals.user_portfolio_rebalance_save, UserPortfolioRebalance),
    (signals.user_portfolio_post_save, UserPortfolio),
]


class LifecycleSignalIsolationMixin:
    """Disable legacy save signals while lifecycle tests create fixtures."""

    @classmethod
    def setUpClass(cls) -> None:
        """Disconnect legacy post-save receivers for isolated tests."""
        super().setUpClass()
        for receiver, sender in SIGNAL_RECEIVERS:
            post_save.disconnect(receiver=receiver, sender=sender)

    @classmethod
    def tearDownClass(cls) -> None:
        """Reconnect legacy post-save receivers after isolated tests."""
        for receiver, sender in SIGNAL_RECEIVERS:
            post_save.connect(receiver=receiver, sender=sender)
        super().tearDownClass()


def create_user_portfolio(**overrides: object) -> UserPortfolio:
    """Create a minimal portfolio parent for rebalance fixtures."""
    values = {
        "user_id": "user-1",
        "broker": BrokerEnum.PAPER_TRADE.value,
        "name": "Lifecycle Test Portfolio",
        "portfolio_id": "portfolio-1",
        "product_type": ProductTypes.EQUITY.value,
        "subscription_id": "subscription-1",
    }
    values.update(overrides)
    return UserPortfolio.objects.create(**values)


def create_rebalance(**overrides: object) -> UserPortfolioRebalance:
    """Create a minimal rebalance event fixture."""
    values = {
        "user_portfolio": create_user_portfolio(),
        "type": RebalanceTypes.INITIAL.value,
        "states": [],
        "current_state": overrides.pop(
            "current_state",
            States.PENDING.value,
        ),
        "transaction_type": CashTransaction.ADD.value,
    }
    values.update(overrides)
    return UserPortfolioRebalance.objects.create(**values)


def create_phase(
    **overrides: object,
) -> PortfolioRebalanceTransaction:
    """Create a minimal rebalance transaction phase fixture."""
    values = {
        "portfolio_rebalance": create_rebalance(),
        "type": RebalanceTransactionTypes.INITIAL.value,
        "current_state": overrides.pop(
            "current_state",
            RebalanceTransactionStates.PROCESSING.value,
        ),
        "executed_list": [],
    }
    values.update(overrides)
    return PortfolioRebalanceTransaction.objects.create(**values)


def create_basket(**overrides: object) -> Basket:
    """Create a minimal basket fixture."""
    values = {
        "user_id": "user-1",
        "current_state": overrides.pop(
            "current_state",
            BasketStates.UNINVESTED.value,
        ),
        "broker": BrokerEnum.PAPER_TRADE.value,
        "model_id": "model-1",
        "payment_id": "payment-1",
        "recommendation_id": 1,
        "user_allocation": [],
        "basket_type": BasketTypes.NORMAL.value,
        "product_type": ProductTypes.MTF.value,
    }
    values.update(overrides)
    return Basket.objects.create(**values)


def create_order(**overrides: object) -> Order:
    """Create a minimal order fixture."""
    values = {
        "basket": create_basket(),
        "trading_symbol": "ABC",
        "current_status": overrides.pop(
            "current_status",
            OrderCurrentStatus.WAITING.value,
        ),
        "states": [],
        "leverage": 1.0,
    }
    values.update(overrides)
    return Order.objects.create(**values)
