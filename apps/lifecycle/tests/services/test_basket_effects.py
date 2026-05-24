"""Tests for Basket side-effect extraction."""

from __future__ import annotations

from django.test import TestCase

from apps.lifecycle.services import apply_basket_effects
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_basket,
)
from apps.portfolio import signals
from apps.portfolio.constants import OrderCurrentStatus, Side
from apps.portfolio.models import Basket, Order


class BasketEffectsTests(LifecycleSignalIsolationMixin, TestCase):
    """Verify extracted Basket save effects match legacy behavior."""

    def test_create_path_creates_orders_from_allocation(self) -> None:
        """Assert allocation creates one order per symbol."""
        basket = create_basket(
            user_allocation=[
                {
                    "symbol": "ABC",
                    "quantity": 1,
                    "side": Side.BUY.value,
                    "stop_loss": 90,
                    "leverage": 2,
                },
            ],
        )

        apply_basket_effects(basket, created=True)

        order = Order.objects.get(basket=basket, trading_symbol="ABC")
        self.assertEqual(order.stop_loss, 90)
        self.assertEqual(order.leverage, 2)
        self.assertEqual(
            order.states,
            OrderCurrentStatus.STATES_WITH_SL.value,
        )

    def test_update_existing_order_updates_fields(self) -> None:
        """Assert existing order is updated instead of duplicated."""
        basket = create_basket(
            user_allocation=[
                {
                    "symbol": "ABC",
                    "quantity": 1,
                    "side": Side.BUY.value,
                    "stop_loss": None,
                    "leverage": 3,
                },
            ],
        )
        Order.objects.create(
            basket=basket,
            trading_symbol="ABC",
            leverage=1,
            states=[],
        )

        apply_basket_effects(basket, created=False)

        self.assertEqual(Order.objects.filter(basket=basket).count(), 1)
        order = Order.objects.get(basket=basket, trading_symbol="ABC")
        self.assertIsNone(order.stop_loss)
        self.assertEqual(order.leverage, 3)
        self.assertEqual(
            order.states,
            OrderCurrentStatus.STATES_WITHOUT_SL.value,
        )

    def test_update_no_allocation_is_noop(self) -> None:
        """Assert empty allocation does not create orders."""
        basket = create_basket(user_allocation=[])

        apply_basket_effects(basket, created=False)

        self.assertEqual(Order.objects.filter(basket=basket).count(), 0)

    def test_service_matches_signal_for_create(self) -> None:
        """Assert direct receiver and service create matching orders."""
        allocation = [
            {
                "symbol": "ABC",
                "quantity": 1,
                "side": Side.BUY.value,
                "stop_loss": 90,
                "leverage": 2,
            },
        ]
        signal_basket = create_basket(user_allocation=allocation)
        service_basket = create_basket(user_allocation=allocation)

        signals.user_basket_save(
            sender=Basket,
            instance=signal_basket,
            created=True,
        )
        apply_basket_effects(service_basket, created=True)

        signal_order = Order.objects.get(basket=signal_basket)
        service_order = Order.objects.get(basket=service_basket)
        self.assertEqual(
            service_order.trading_symbol,
            signal_order.trading_symbol,
        )
        self.assertEqual(service_order.stop_loss, signal_order.stop_loss)
        self.assertEqual(service_order.states, signal_order.states)
