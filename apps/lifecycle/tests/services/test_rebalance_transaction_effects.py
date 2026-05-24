"""Tests for PortfolioRebalanceTransaction side-effect extraction."""

from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase

from apps.lifecycle.services import apply_rebalance_transaction_effects
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_phase,
)
from apps.portfolio import signals
from apps.portfolio.constants import (
    OrderStatus,
    RebalanceTransactionStates,
    RebalanceTransactionTypes,
    Side,
    States,
)
from apps.portfolio.models import (
    PortfolioRebalanceTransaction,
    UserInstruction,
)


class RebalanceTransactionEffectsTests(
    LifecycleSignalIsolationMixin,
    TestCase,
):
    """Verify extracted PRT save effects match legacy signal behavior."""

    def test_create_path_creates_user_instructions(self) -> None:
        """Assert creation delegates to legacy instruction creation."""
        phase = create_phase(
            allocation_quantity=[
                {
                    "symbol": "ABC",
                    "quantity": 2,
                    "side": Side.BUY.value,
                },
            ],
        )

        apply_rebalance_transaction_effects(phase, created=True)

        instruction = UserInstruction.objects.get(
            portfolio_rebalance_transaction=phase,
        )
        self.assertEqual(instruction.symbol, "ABC")
        self.assertEqual(instruction.status, OrderStatus.WAITING.value)

    @patch(
        "apps.portfolio.services.user_portfolio_rebalance"
        ".send_investment_succeeded_event.delay",
    )
    def test_update_terminal_updates_parent_rebalance(
        self,
        _send_event: object,
    ) -> None:
        """Assert terminal phase status updates the parent rebalance."""
        phase = create_phase(
            current_state=RebalanceTransactionStates.COMPLETED.value,
            type=RebalanceTransactionTypes.INITIAL.value,
        )

        apply_rebalance_transaction_effects(phase, created=False)

        phase.portfolio_rebalance.refresh_from_db()
        self.assertEqual(
            phase.portfolio_rebalance.current_state,
            States.COMPLETE.value,
        )

    def test_update_non_terminal_is_noop_for_parent(self) -> None:
        """Assert non-terminal phase status leaves parent unchanged."""
        phase = create_phase(
            current_state=RebalanceTransactionStates.PROCESSING.value,
        )

        apply_rebalance_transaction_effects(phase, created=False)

        phase.portfolio_rebalance.refresh_from_db()
        self.assertEqual(
            phase.portfolio_rebalance.current_state,
            States.PENDING.value,
        )

    @patch(
        "apps.portfolio.services.user_portfolio_rebalance"
        ".send_investment_succeeded_event.delay",
    )
    def test_service_matches_signal_for_terminal_update(
        self,
        _send_event: object,
    ) -> None:
        """Assert direct receiver and extracted service write same state."""
        signal_phase = create_phase(
            current_state=RebalanceTransactionStates.COMPLETED.value,
            type=RebalanceTransactionTypes.INITIAL.value,
        )
        service_phase = create_phase(
            current_state=RebalanceTransactionStates.COMPLETED.value,
            type=RebalanceTransactionTypes.INITIAL.value,
        )

        signals.rebalance_transaction_save(
            sender=PortfolioRebalanceTransaction,
            instance=signal_phase,
            created=False,
        )
        apply_rebalance_transaction_effects(service_phase, created=False)

        signal_phase.portfolio_rebalance.refresh_from_db()
        service_phase.portfolio_rebalance.refresh_from_db()
        self.assertEqual(
            service_phase.portfolio_rebalance.current_state,
            signal_phase.portfolio_rebalance.current_state,
        )
