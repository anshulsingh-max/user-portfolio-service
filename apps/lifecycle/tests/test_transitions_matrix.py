"""Tests for the exhaustive lifecycle transition matrix."""

from __future__ import annotations

from django.test import SimpleTestCase

from apps.lifecycle.constants import CallbackStageType
from apps.portfolio.constants import (
    BasketStates,
    OrderCurrentStatus,
    RebalanceTransactionStates,
    States,
)
from apps.lifecycle.transitions import (
    ALLOWED,
    INITIAL_STATES,
    is_allowed,
    is_terminal,
)


class TransitionMatrixTests(SimpleTestCase):
    """Protect the documented Phase 1 transition rules from drift."""

    def test_every_listed_transition_is_allowed(self) -> None:
        """Assert all matrix entries are accepted by the helper."""
        for stage_type, transitions in ALLOWED.items():
            for from_state, to_states in transitions.items():
                for to_state in to_states:
                    self.assertTrue(
                        is_allowed(stage_type, from_state, to_state),
                        f"{stage_type}: {from_state} -> {to_state}",
                    )

    def test_initial_states_allow_creation_from_none(self) -> None:
        """Assert None only maps to each flow's documented initial state."""
        for stage_type, initial_state in INITIAL_STATES.items():
            self.assertTrue(is_allowed(stage_type, None, initial_state))
            for state in ALLOWED[stage_type]:
                if state != initial_state:
                    self.assertFalse(is_allowed(stage_type, None, state))

    def test_non_listed_transitions_are_rejected(self) -> None:
        """Assert representative illegal moves remain blocked."""
        illegal = [
            (
                CallbackStageType.REBALANCE_EVENT.value,
                States.COMPLETE.value,
                States.PARTIAL.value,
            ),
            (
                CallbackStageType.PHASE.value,
                RebalanceTransactionStates.COMPLETED.value,
                RebalanceTransactionStates.PROCESSING.value,
            ),
            (
                CallbackStageType.ORDER.value,
                OrderCurrentStatus.WAITING.value,
                OrderCurrentStatus.SELL.value,
            ),
            (
                CallbackStageType.BASKET.value,
                BasketStates.MONITORING.value,
                BasketStates.WAITING.value,
            ),
        ]
        for stage_type, from_state, to_state in illegal:
            self.assertFalse(is_allowed(stage_type, from_state, to_state))

    def test_terminal_states_have_no_outgoing_transitions(self) -> None:
        """Assert each terminal state has an empty outgoing list."""
        terminal_states = [
            (CallbackStageType.REBALANCE_EVENT.value, States.COMPLETE.value),
            (
                CallbackStageType.PHASE.value,
                RebalanceTransactionStates.COMPLETED.value,
            ),
            (
                CallbackStageType.PHASE.value,
                RebalanceTransactionStates.MANUALLY_COMPLETED.value,
            ),
            (
                CallbackStageType.PHASE.value,
                RebalanceTransactionStates.SKIPPED.value,
            ),
            (CallbackStageType.ORDER.value, OrderCurrentStatus.SELL.value),
            (CallbackStageType.ORDER.value, OrderCurrentStatus.SKIP.value),
            (CallbackStageType.BASKET.value, BasketStates.COMPLETE.value),
        ]
        for stage_type, state in terminal_states:
            self.assertEqual(ALLOWED[stage_type][state], [])
            self.assertTrue(is_terminal(stage_type, state))

    def test_non_terminal_states_are_reported(self) -> None:
        """Assert non-terminal states are not mistaken for final states."""
        non_terminal_states = [
            (CallbackStageType.REBALANCE_EVENT.value, States.PENDING.value),
            (
                CallbackStageType.PHASE.value,
                RebalanceTransactionStates.PROCESSING.value,
            ),
            (CallbackStageType.ORDER.value, OrderCurrentStatus.BUY.value),
            (CallbackStageType.BASKET.value, BasketStates.WAITING.value),
        ]
        for stage_type, state in non_terminal_states:
            self.assertFalse(is_terminal(stage_type, state))
