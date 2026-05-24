"""Tests for OrderInstruction side-effect extraction."""

from __future__ import annotations

from django.test import TestCase

from apps.lifecycle.services import apply_order_instruction_effects
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_order,
    create_order_instruction,
)
from apps.portfolio import signals
from apps.portfolio.constants import OrderCurrentStatus, OrderStatus, Side
from apps.portfolio.models import OrderInstruction


class OrderInstructionEffectsTests(
    LifecycleSignalIsolationMixin,
    TestCase,
):
    """Verify extracted OrderInstruction save effects preserve parity."""

    def test_create_path_updates_order_status(self) -> None:
        """Assert created WAITING BUY moves order to buy_in_progress."""
        instruction = create_order_instruction(
            side=Side.BUY.value,
            status=OrderStatus.WAITING.value,
        )

        apply_order_instruction_effects(instruction, created=True)

        instruction.order.refresh_from_db()
        self.assertEqual(
            instruction.order.current_status,
            OrderCurrentStatus.BUY_IN_PROGRESS.value,
        )

    def test_update_filled_recomputes_price_amount_and_status(self) -> None:
        """Assert FILLED BUY writes price, amounts, and next status."""
        instruction = create_order_instruction(
            side=Side.BUY.value,
            status=OrderStatus.FILLED.value,
            value=120,
            order_price=12,
            filled_quantity=10,
        )

        apply_order_instruction_effects(instruction, created=False)

        instruction.order.refresh_from_db()
        self.assertEqual(instruction.order.buy_price, 12)
        self.assertEqual(instruction.order.initial_amount, 120)
        self.assertEqual(instruction.order.end_amount, 0)
        self.assertEqual(
            instruction.order.current_status,
            OrderCurrentStatus.BUY.value,
        )

    def test_update_non_terminal_is_noop(self) -> None:
        """Assert WAITING update leaves order amounts unchanged."""
        order = create_order(current_status=OrderCurrentStatus.WAITING.value)
        instruction = create_order_instruction(
            order=order,
            side=Side.BUY.value,
            status=OrderStatus.WAITING.value,
            value=120,
            order_price=12,
        )

        apply_order_instruction_effects(instruction, created=False)

        order.refresh_from_db()
        self.assertIsNone(order.initial_amount)
        self.assertEqual(
            order.current_status,
            OrderCurrentStatus.WAITING.value,
        )

    def test_service_matches_signal_for_filled_update(self) -> None:
        """Assert direct receiver and service update equivalent order state."""
        signal_order = create_order(trading_symbol="SIG")
        service_order = create_order(trading_symbol="SRV")
        signal_instruction = create_order_instruction(
            order=signal_order,
            order_tag="signal-filled",
            symbol="SIG",
            side=Side.BUY.value,
            status=OrderStatus.FILLED.value,
            value=100,
            order_price=10,
            filled_quantity=10,
        )
        service_instruction = create_order_instruction(
            order=service_order,
            order_tag="service-filled",
            symbol="SRV",
            side=Side.BUY.value,
            status=OrderStatus.FILLED.value,
            value=100,
            order_price=10,
            filled_quantity=10,
        )

        signals.order_instruction_save(
            sender=OrderInstruction,
            instance=signal_instruction,
            created=False,
        )
        apply_order_instruction_effects(service_instruction, created=False)

        signal_order.refresh_from_db()
        service_order.refresh_from_db()
        self.assertEqual(service_order.buy_price, signal_order.buy_price)
        self.assertEqual(
            service_order.initial_amount,
            signal_order.initial_amount,
        )
        self.assertEqual(
            service_order.current_status,
            signal_order.current_status,
        )
