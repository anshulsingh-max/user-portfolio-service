"""Adapters over legacy lifecycle models.

Each adapter hides state field names and parent lookups so the transition
authority never writes directly to model-specific lifecycle attributes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from django.db import models

from apps.lifecycle.constants import CallbackStageType
from apps.portfolio.models.basket import Basket
from apps.portfolio.models.orders import Order
from apps.portfolio.models.portfolio_rebealnce_transaction import (
    PortfolioRebalanceTransaction,
)
from apps.portfolio.models.user_portfolio_rebalance import (
    UserPortfolioRebalance,
)


class StageAdapter(ABC):
    """Uniform lock/read/write contract over non-uniform legacy models."""

    stage_type: ClassVar[str]
    model: ClassVar[type[models.Model]]
    state_field: ClassVar[str]

    @abstractmethod
    def lock_for_update(self, stage: models.Model) -> models.Model:
        """Return a row-locked fresh instance for serialised callbacks."""

    @abstractmethod
    def get_state(self, stage: models.Model) -> str:
        """Read the model-specific lifecycle state through one API."""

    @abstractmethod
    def set_state(self, stage: models.Model, value: str) -> None:
        """Persist the model-specific lifecycle state through one API."""

    @abstractmethod
    def parent(self, stage: models.Model) -> Any:
        """Return the owning lifecycle parent for hierarchy traversal."""


class RebalanceEventAdapter(StageAdapter):
    """Adapter for the rebalance event lifecycle row."""

    stage_type = CallbackStageType.REBALANCE_EVENT.value
    model = UserPortfolioRebalance
    state_field = "current_state"

    def lock_for_update(self, stage: UserPortfolioRebalance) -> models.Model:
        """Return the locked rebalance event instance."""
        return self.model.objects.select_for_update().get(pk=stage.pk)

    def get_state(self, stage: UserPortfolioRebalance) -> str:
        """Read the rebalance event state field."""
        return getattr(stage, self.state_field)

    def set_state(self, stage: UserPortfolioRebalance, value: str) -> None:
        """Persist the rebalance event state field."""
        setattr(stage, self.state_field, value)
        stage.save(update_fields=[self.state_field, "modified"])

    def parent(self, stage: UserPortfolioRebalance) -> models.Model:
        """Return the owning user portfolio."""
        return stage.user_portfolio


class PhaseAdapter(StageAdapter):
    """Adapter for the rebalance transaction phase lifecycle row."""

    stage_type = CallbackStageType.PHASE.value
    model = PortfolioRebalanceTransaction
    state_field = "current_state"

    def lock_for_update(
        self,
        stage: PortfolioRebalanceTransaction,
    ) -> models.Model:
        """Return the locked phase instance."""
        return self.model.objects.select_for_update().get(pk=stage.pk)

    def get_state(self, stage: PortfolioRebalanceTransaction) -> str:
        """Read the phase state field."""
        return getattr(stage, self.state_field)

    def set_state(
        self,
        stage: PortfolioRebalanceTransaction,
        value: str,
    ) -> None:
        """Persist the phase state field."""
        setattr(stage, self.state_field, value)
        stage.save(update_fields=[self.state_field, "modified"])

    def parent(self, stage: PortfolioRebalanceTransaction) -> models.Model:
        """Return the owning rebalance event."""
        return stage.portfolio_rebalance


class OrderAdapter(StageAdapter):
    """Adapter for basket order lifecycle rows."""

    stage_type = CallbackStageType.ORDER.value
    model = Order
    state_field = "current_status"

    def lock_for_update(self, stage: Order) -> models.Model:
        """Return the locked order instance."""
        return self.model.objects.select_for_update().get(pk=stage.pk)

    def get_state(self, stage: Order) -> str:
        """Read the order status field."""
        return getattr(stage, self.state_field)

    def set_state(self, stage: Order, value: str) -> None:
        """Persist the order status field."""
        setattr(stage, self.state_field, value)
        stage.save(update_fields=[self.state_field, "modified"])

    def parent(self, stage: Order) -> models.Model:
        """Return the owning basket."""
        return stage.basket


class BasketAdapter(StageAdapter):
    """Adapter for root basket lifecycle rows."""

    stage_type = CallbackStageType.BASKET.value
    model = Basket
    state_field = "current_state"

    def lock_for_update(self, stage: Basket) -> models.Model:
        """Return the locked basket instance."""
        return self.model.objects.select_for_update().get(pk=stage.pk)

    def get_state(self, stage: Basket) -> str:
        """Read the basket state field."""
        return getattr(stage, self.state_field)

    def set_state(self, stage: Basket, value: str) -> None:
        """Persist the basket state field."""
        setattr(stage, self.state_field, value)
        stage.save(update_fields=[self.state_field, "modified"])

    def parent(self, stage: Basket) -> None:
        """Return no parent because basket is a root lifecycle stage."""
        return None


_ADAPTERS: dict[type[models.Model], StageAdapter] = {
    UserPortfolioRebalance: RebalanceEventAdapter(),
    PortfolioRebalanceTransaction: PhaseAdapter(),
    Order: OrderAdapter(),
    Basket: BasketAdapter(),
}


def get_adapter(stage: models.Model) -> StageAdapter:
    """Resolve an adapter by concrete Python type, not model attributes."""
    try:
        return _ADAPTERS[type(stage)]
    except KeyError as exc:
        raise TypeError(
            f"No StageAdapter registered for {type(stage).__name__}"
        ) from exc
