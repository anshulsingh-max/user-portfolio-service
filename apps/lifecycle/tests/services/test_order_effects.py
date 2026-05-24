"""Tests for Order side-effect extraction."""

from __future__ import annotations

from django.test import TestCase

from apps.lifecycle.services import apply_order_effects
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_basket,
    create_order,
)
from apps.portfolio import signals
from apps.portfolio.constants import BasketStates, OrderCurrentStatus, Side
from apps.portfolio.models import Order, OrderInstruction


class OrderEffectsTests(LifecycleSignalIsolationMixin, TestCase):
    """Verify extracted Order save effects match legacy behavior."""

    def test_create_path_creates_matching_instruction(self) -> None:
        """Assert created order creates instructions from basket allocation."""
        basket = create_basket(
            user_allocation=[
                {
                    "symbol": "ABC",
                    "quantity": 4,
                    "side": Side.BUY.value,
                },
            ],
        )
        order = create_order(basket=basket, trading_symbol="ABC")

        apply_order_effects(order, created=True)

        instruction = OrderInstruction.objects.get(order=order)
        self.assertEqual(instruction.order_tag, f"{order.id}_ABC_buy")
        self.assertEqual(instruction.quantity, 4)

    def test_update_terminal_status_updates_basket_details(self) -> None:
        """Assert BUY status recomputes basket totals and state."""
        basket = create_basket(profit_target_1=10)
        order = create_order(
            basket=basket,
            current_status=OrderCurrentStatus.BUY.value,
            initial_amount=100,
        )

        apply_order_effects(order, created=False)

        basket.refresh_from_db()
        self.assertEqual(basket.amount, 100)
        self.assertAlmostEqual(basket.profit_target_1_value, 110)
        self.assertEqual(basket.current_state, BasketStates.MONITORING.value)

    def test_update_non_terminal_is_noop(self) -> None:
        """Assert WAITING status does not update basket details."""
        basket = create_basket()
        order = create_order(
            basket=basket,
            current_status=OrderCurrentStatus.WAITING.value,
            initial_amount=100,
        )

        apply_order_effects(order, created=False)

        basket.refresh_from_db()
        self.assertIsNone(basket.amount)
        self.assertEqual(basket.current_state, BasketStates.UNINVESTED.value)

    def test_service_matches_signal_for_create(self) -> None:
        """Assert direct receiver and service create equivalent rows."""
        signal_basket = create_basket(
            user_allocation=[
                {
                    "symbol": "ABC",
                    "quantity": 4,
                    "side": Side.BUY.value,
                },
            ],
        )
        service_basket = create_basket(
            user_allocation=[
                {
                    "symbol": "ABC",
                    "quantity": 4,
                    "side": Side.BUY.value,
                },
            ],
        )
        signal_order = create_order(basket=signal_basket, trading_symbol="ABC")
        service_order = create_order(
            basket=service_basket,
            trading_symbol="ABC",
        )

        signals.orders_save(
            sender=Order,
            instance=signal_order,
            created=True,
        )
        apply_order_effects(service_order, created=True)

        signal_instruction = OrderInstruction.objects.get(order=signal_order)
        service_instruction = OrderInstruction.objects.get(order=service_order)
        self.assertEqual(service_instruction.symbol, signal_instruction.symbol)
        self.assertEqual(
            service_instruction.quantity,
            signal_instruction.quantity,
        )
