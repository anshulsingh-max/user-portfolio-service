"""Tests for the lifecycle transition service."""

from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase, TransactionTestCase

from apps.lifecycle.constants import (
    CallbackDirection,
    CallbackLogStatus,
    CallbackStageType,
    LifecycleEventTrigger,
)
from apps.portfolio.constants import (
    OrderCurrentStatus,
    States,
)
from apps.lifecycle.exceptions import IllegalTransition
from apps.lifecycle.models import LifecycleEvent
from apps.lifecycle.service import transition
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_order,
    create_rebalance,
)
from apps.lifecycle.models import CallbackLog


class TransitionServiceTests(LifecycleSignalIsolationMixin, TestCase):
    """Verify state writes, event rows, and idempotency behavior."""

    def test_legal_transition_updates_state_and_creates_event(self) -> None:
        """Assert a legal transition writes state and append-only history."""
        stage = create_rebalance()

        transition(
            stage,
            States.PARTIAL.value,
            actor="tester",
            trigger=LifecycleEventTrigger.MANUAL.value,
            payload={"source": "unit"},
        )

        stage.refresh_from_db()
        event = LifecycleEvent.objects.get()
        self.assertEqual(stage.current_state, States.PARTIAL.value)
        self.assertEqual(event.from_state, States.PENDING.value)
        self.assertEqual(event.to_state, States.PARTIAL.value)
        self.assertEqual(event.actor, "tester")
        self.assertEqual(event.trigger, LifecycleEventTrigger.MANUAL.value)

    def test_illegal_transition_raises_without_mutating(self) -> None:
        """Assert matrix violations do not write state or history."""
        stage = create_rebalance(current_state=States.COMPLETE.value)

        with self.assertRaises(IllegalTransition):
            transition(
                stage,
                States.PARTIAL.value,
                actor="tester",
                trigger=LifecycleEventTrigger.MANUAL.value,
            )

        stage.refresh_from_db()
        self.assertEqual(stage.current_state, States.COMPLETE.value)
        self.assertEqual(LifecycleEvent.objects.count(), 0)

    def test_completed_callback_log_dedups_transition(self) -> None:
        """Assert completed idempotency records short-circuit transition."""
        stage = create_order()
        key = "idem-1"
        CallbackLog.objects.create(
            stage_type=CallbackStageType.ORDER.value,
            stage_id=stage.pk,
            callback_ref="callback-1",
            direction=CallbackDirection.INBOUND.value,
            target_service="trade-placement",
            status=CallbackLogStatus.COMPLETED.value,
            idempotency_key=key,
        )

        transition(
            stage,
            OrderCurrentStatus.BUY_IN_PROGRESS.value,
            actor="callback",
            trigger=LifecycleEventTrigger.CALLBACK.value,
            idempotency_key=key,
        )

        stage.refresh_from_db()
        self.assertEqual(
            stage.current_status,
            OrderCurrentStatus.WAITING.value,
        )
        self.assertEqual(LifecycleEvent.objects.count(), 0)

    def test_missing_completed_callback_log_allows_transition(self) -> None:
        """Assert non-duplicate idempotency keys do not block state writes."""
        stage = create_order()

        transition(
            stage,
            OrderCurrentStatus.BUY_IN_PROGRESS.value,
            actor="callback",
            trigger=LifecycleEventTrigger.CALLBACK.value,
            idempotency_key="new-key",
        )

        stage.refresh_from_db()
        self.assertEqual(
            stage.current_status,
            OrderCurrentStatus.BUY_IN_PROGRESS.value,
        )
        self.assertEqual(LifecycleEvent.objects.count(), 1)

    def test_on_commit_is_deferred_inside_testcase_transaction(self) -> None:
        """Assert side effects do not run before the outer test commits."""
        stage = create_rebalance()

        with patch(
            "apps.lifecycle.service._schedule_side_effects",
        ) as schedule:
            transition(
                stage,
                States.PARTIAL.value,
                actor="tester",
                trigger=LifecycleEventTrigger.MANUAL.value,
            )
            schedule.assert_not_called()


class TransitionServiceCommitTests(
    LifecycleSignalIsolationMixin,
    TransactionTestCase,
):
    """Verify on_commit hooks run when a real transaction commits."""

    def test_on_commit_runs_after_transition_commit(self) -> None:
        """Assert side-effect scheduling happens after the atomic block."""
        stage = create_rebalance()

        with patch(
            "apps.lifecycle.service._schedule_side_effects",
        ) as schedule:
            transition(
                stage,
                States.PARTIAL.value,
                actor="tester",
                trigger=LifecycleEventTrigger.MANUAL.value,
            )
            schedule.assert_called_once_with(
                CallbackStageType.REBALANCE_EVENT.value,
                stage.pk,
                States.PARTIAL.value,
            )
