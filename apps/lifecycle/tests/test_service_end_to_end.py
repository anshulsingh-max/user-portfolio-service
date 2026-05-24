"""End-to-end lifecycle foundation tests for both product flows."""

from __future__ import annotations

from django.test import TransactionTestCase

from apps.lifecycle.constants import (
    CallbackStageType,
    LifecycleEventTrigger,
    LifecycleEventType,
)
from apps.portfolio.constants import (
    BasketStates,
    States,
)
from apps.lifecycle.exceptions import IllegalTransition
from apps.lifecycle.models import LifecycleEvent
from apps.lifecycle.service import transition
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_basket,
    create_rebalance,
)
from apps.lifecycle.transitions import is_allowed, is_terminal


class LifecycleEndToEndTests(
    LifecycleSignalIsolationMixin,
    TransactionTestCase,
):
    """Exercise representative Flow A and Flow B lifecycle chains."""

    def test_rebalance_flow_reaches_terminal_state(self) -> None:
        """Assert rebalance event can progress pending to complete."""
        stage = create_rebalance()
        LifecycleEvent.objects.create(
            stage_type=CallbackStageType.REBALANCE_EVENT.value,
            stage_id=stage.pk,
            event_type=LifecycleEventType.CREATED.value,
            to_state=States.PENDING.value,
            actor="tester",
            trigger=LifecycleEventTrigger.SYSTEM.value,
        )

        transition(
            stage,
            States.PARTIAL.value,
            actor="tester",
            trigger=LifecycleEventTrigger.MANUAL.value,
        )
        transition(
            stage,
            States.COMPLETE.value,
            actor="tester",
            trigger=LifecycleEventTrigger.MANUAL.value,
        )

        stage.refresh_from_db()
        self.assertEqual(stage.current_state, States.COMPLETE.value)
        self.assertEqual(LifecycleEvent.objects.count(), 3)
        self.assertTrue(
            is_terminal(
                CallbackStageType.REBALANCE_EVENT.value,
                States.COMPLETE.value,
            )
        )
        self.assertFalse(
            is_allowed(
                CallbackStageType.REBALANCE_EVENT.value,
                States.COMPLETE.value,
                States.PARTIAL.value,
            )
        )
        with self.assertRaises(IllegalTransition):
            transition(
                stage,
                States.PARTIAL.value,
                actor="tester",
                trigger=LifecycleEventTrigger.MANUAL.value,
            )

    def test_basket_flow_reaches_terminal_state(self) -> None:
        """Assert basket can progress uninvested to complete."""
        stage = create_basket()

        transition(
            stage,
            BasketStates.WAITING.value,
            actor="tester",
            trigger=LifecycleEventTrigger.MANUAL.value,
        )
        transition(
            stage,
            BasketStates.MONITORING.value,
            actor="tester",
            trigger=LifecycleEventTrigger.MANUAL.value,
        )
        transition(
            stage,
            BasketStates.COMPLETE.value,
            actor="tester",
            trigger=LifecycleEventTrigger.MANUAL.value,
        )

        stage.refresh_from_db()
        self.assertEqual(stage.current_state, BasketStates.COMPLETE.value)
        self.assertEqual(LifecycleEvent.objects.count(), 3)
        self.assertTrue(
            is_terminal(
                CallbackStageType.BASKET.value,
                BasketStates.COMPLETE.value,
            )
        )
