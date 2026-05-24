"""Tests for UserInstruction side-effect extraction."""

from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase

from apps.holdings.models import Holding
from apps.lifecycle.services import apply_user_instruction_effects
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_phase,
    create_user_instruction,
)
from apps.portfolio import signals
from apps.portfolio.constants import Asset, OrderStatus, Side
from apps.portfolio.models import UserInstruction


class UserInstructionEffectsTests(LifecycleSignalIsolationMixin, TestCase):
    """Verify extracted UserInstruction save effects preserve parity."""

    def test_create_path_sets_order_tag_and_aggregates(self) -> None:
        """Assert creation stamps the row with its own id."""
        instruction = create_user_instruction(order_tag="create-path")

        apply_user_instruction_effects(instruction, created=True)

        instruction.refresh_from_db()
        self.assertEqual(instruction.order_tag, str(instruction.id))
        instruction.portfolio_rebalance_transaction.refresh_from_db()
        self.assertEqual(
            instruction.portfolio_rebalance_transaction.executed_list,
            [],
        )

    @patch(
        "apps.lifecycle.services.user_instruction_effects"
        ".phase_detail_callback.delay",
    )
    def test_update_terminal_filled_updates_holdings_and_dispatches_sell(
        self,
        phase_detail_delay: object,
    ) -> None:
        """Assert FILLED SELL updates holdings, cash, PRT, and callback."""
        instruction = create_user_instruction(
            order_tag="sell-fill",
            symbol="XYZ",
            quantity=5,
            filled_quantity=5,
            side=Side.SELL.value,
            value=250,
            status=OrderStatus.FILLED.value,
        )

        apply_user_instruction_effects(instruction, created=False)

        portfolio = (
            instruction.portfolio_rebalance_transaction
            .portfolio_rebalance
            .user_portfolio
        )
        symbol_holding = Holding.objects.get(
            user_portfolio=portfolio,
            symbol="XYZ",
        )
        cash_holding = Holding.objects.get(
            user_portfolio=portfolio,
            symbol=Asset.CASH.value,
        )
        self.assertEqual(symbol_holding.quantity, -5)
        self.assertEqual(cash_holding.quantity, 250)
        phase_detail_delay.assert_called_once()
        instruction.portfolio_rebalance_transaction.refresh_from_db()
        self.assertEqual(
            instruction.portfolio_rebalance_transaction.executed_list,
            ["XYZ"],
        )
        self.assertEqual(
            instruction.portfolio_rebalance_transaction.amount,
            250,
        )

    def test_update_terminal_non_filled_refreshes_without_holdings(
        self,
    ) -> None:
        """Assert CANCEL refreshes PRT without writing holdings."""
        instruction = create_user_instruction(
            order_tag="cancelled",
            status=OrderStatus.CANCEL.value,
        )

        apply_user_instruction_effects(instruction, created=False)

        self.assertEqual(Holding.objects.count(), 0)
        instruction.portfolio_rebalance_transaction.refresh_from_db()
        self.assertEqual(
            instruction.portfolio_rebalance_transaction.executed_list,
            [],
        )

    def test_update_non_terminal_only_aggregates_existing_fills(self) -> None:
        """Assert WAITING skips holdings and refresh branches."""
        phase = create_phase()
        create_user_instruction(
            portfolio_rebalance_transaction=phase,
            order_tag="filled-existing",
            symbol="ABC",
            value=100,
            status=OrderStatus.FILLED.value,
        )
        instruction = create_user_instruction(
            portfolio_rebalance_transaction=phase,
            order_tag="waiting-existing",
            status=OrderStatus.WAITING.value,
        )

        apply_user_instruction_effects(instruction, created=False)

        self.assertEqual(Holding.objects.count(), 0)
        phase.refresh_from_db()
        self.assertEqual(phase.executed_list, ["ABC"])
        self.assertEqual(phase.amount, 100)

    @patch(
        "apps.lifecycle.services.user_instruction_effects"
        ".phase_detail_callback.delay",
    )
    @patch("apps.portfolio.signals.phase_detail_callback.delay")
    def test_service_matches_signal_for_sell_fill(
        self,
        _signal_delay: object,
        _service_delay: object,
    ) -> None:
        """Assert direct receiver and service write equivalent DB state."""
        signal_instruction = create_user_instruction(
            order_tag="signal-sell",
            symbol="SELLA",
            quantity=5,
            filled_quantity=5,
            side=Side.SELL.value,
            value=200,
            status=OrderStatus.FILLED.value,
        )
        service_instruction = create_user_instruction(
            order_tag="service-sell",
            symbol="SELLA",
            quantity=5,
            filled_quantity=5,
            side=Side.SELL.value,
            value=200,
            status=OrderStatus.FILLED.value,
        )

        signals.user_instructions_save(
            sender=UserInstruction,
            instance=signal_instruction,
            created=False,
        )
        apply_user_instruction_effects(service_instruction, created=False)

        signal_prt = signal_instruction.portfolio_rebalance_transaction
        service_prt = service_instruction.portfolio_rebalance_transaction
        signal_prt.refresh_from_db()
        service_prt.refresh_from_db()
        self.assertEqual(service_prt.executed_list, signal_prt.executed_list)
        self.assertEqual(service_prt.amount, signal_prt.amount)
