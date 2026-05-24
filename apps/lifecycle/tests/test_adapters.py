"""Tests for lifecycle stage adapters over legacy models."""

from __future__ import annotations

from django.db import transaction
from django.test import TestCase

from apps.portfolio.constants import (
    BasketStates,
    OrderCurrentStatus,
    RebalanceTransactionStates,
    States,
)
from apps.lifecycle.adapters import (
    BasketAdapter,
    OrderAdapter,
    PhaseAdapter,
    RebalanceEventAdapter,
    get_adapter,
)
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_basket,
    create_order,
    create_phase,
    create_rebalance,
    create_user_portfolio,
)


class AdapterTests(LifecycleSignalIsolationMixin, TestCase):
    """Verify adapters lock, read, write, and resolve parents uniformly."""

    def test_rebalance_event_adapter_round_trip(self) -> None:
        """Assert the rebalance adapter handles state and parent access."""
        stage = create_rebalance()
        adapter = RebalanceEventAdapter()
        with transaction.atomic():
            locked = adapter.lock_for_update(stage)
            self.assertEqual(locked.pk, stage.pk)
            self.assertEqual(adapter.get_state(locked), States.PENDING.value)
        adapter.set_state(stage, States.PARTIAL.value)
        stage.refresh_from_db()
        self.assertEqual(stage.current_state, States.PARTIAL.value)
        self.assertEqual(adapter.parent(stage), stage.user_portfolio)

    def test_phase_adapter_round_trip(self) -> None:
        """Assert the phase adapter handles state and parent access."""
        stage = create_phase()
        adapter = PhaseAdapter()
        with transaction.atomic():
            locked = adapter.lock_for_update(stage)
            self.assertEqual(locked.pk, stage.pk)
            self.assertEqual(
                adapter.get_state(locked),
                RebalanceTransactionStates.PROCESSING.value,
            )
        adapter.set_state(
            stage,
            RebalanceTransactionStates.PARTIALLY_COMPLETED.value,
        )
        stage.refresh_from_db()
        self.assertEqual(
            stage.current_state,
            RebalanceTransactionStates.PARTIALLY_COMPLETED.value,
        )
        self.assertEqual(adapter.parent(stage), stage.portfolio_rebalance)

    def test_order_adapter_round_trip(self) -> None:
        """Assert the order adapter handles current_status correctly."""
        stage = create_order()
        adapter = OrderAdapter()
        with transaction.atomic():
            locked = adapter.lock_for_update(stage)
            self.assertEqual(locked.pk, stage.pk)
            self.assertEqual(
                adapter.get_state(locked),
                OrderCurrentStatus.WAITING.value,
            )
        adapter.set_state(stage, OrderCurrentStatus.BUY_IN_PROGRESS.value)
        stage.refresh_from_db()
        self.assertEqual(
            stage.current_status,
            OrderCurrentStatus.BUY_IN_PROGRESS.value,
        )
        self.assertEqual(adapter.parent(stage), stage.basket)

    def test_basket_adapter_round_trip(self) -> None:
        """Assert the basket adapter handles a root lifecycle stage."""
        stage = create_basket()
        adapter = BasketAdapter()
        with transaction.atomic():
            locked = adapter.lock_for_update(stage)
            self.assertEqual(locked.pk, stage.pk)
            self.assertEqual(
                adapter.get_state(locked),
                BasketStates.UNINVESTED.value,
            )
        adapter.set_state(stage, BasketStates.WAITING.value)
        stage.refresh_from_db()
        self.assertEqual(stage.current_state, BasketStates.WAITING.value)
        self.assertIsNone(adapter.parent(stage))

    def test_get_adapter_rejects_unregistered_model(self) -> None:
        """Assert dispatch uses concrete type and rejects unrelated models."""
        with self.assertRaises(TypeError):
            get_adapter(create_user_portfolio())
