"""Tests for UserPortfolioRebalance side-effect extraction."""

from __future__ import annotations

from django.test import TestCase

from apps.lifecycle.services import apply_user_portfolio_rebalance_effects
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_rebalance,
    create_user_portfolio,
)
from apps.portfolio import signals
from apps.portfolio.constants import RebalanceTypes
from apps.portfolio.models import UserPortfolioRebalance


class UserPortfolioRebalanceEffectsTests(
    LifecycleSignalIsolationMixin,
    TestCase,
):
    """Verify extracted UPR save effects preserve legacy behavior."""

    def test_create_cash_allocation_copies_previous_rebalance_id(self) -> None:
        """Assert cash allocation copies last prior rebalance id."""
        portfolio = create_user_portfolio()
        create_rebalance(user_portfolio=portfolio, rebalance_id=123)
        rebalance = create_rebalance(
            user_portfolio=portfolio,
            type=RebalanceTypes.CASH_ALLOCATION.value,
        )

        apply_user_portfolio_rebalance_effects(rebalance, created=True)

        rebalance.refresh_from_db()
        self.assertEqual(rebalance.rebalance_id, 123)

    def test_create_cash_allocation_without_previous_is_noop(self) -> None:
        """Assert first cash allocation has no copied id."""
        rebalance = create_rebalance(
            type=RebalanceTypes.CASH_ALLOCATION.value,
        )

        apply_user_portfolio_rebalance_effects(rebalance, created=True)

        rebalance.refresh_from_db()
        self.assertIsNone(rebalance.rebalance_id)

    def test_update_path_is_noop(self) -> None:
        """Assert update does not copy prior rebalance id."""
        portfolio = create_user_portfolio()
        create_rebalance(user_portfolio=portfolio, rebalance_id=456)
        rebalance = create_rebalance(
            user_portfolio=portfolio,
            type=RebalanceTypes.CASH_ALLOCATION.value,
        )

        apply_user_portfolio_rebalance_effects(rebalance, created=False)

        rebalance.refresh_from_db()
        self.assertIsNone(rebalance.rebalance_id)

    def test_service_matches_signal_for_cash_allocation(self) -> None:
        """Assert direct receiver and service copy the same prior id."""
        signal_portfolio = create_user_portfolio(user_id="signal")
        service_portfolio = create_user_portfolio(user_id="service")
        create_rebalance(user_portfolio=signal_portfolio, rebalance_id=789)
        create_rebalance(user_portfolio=service_portfolio, rebalance_id=789)
        signal_rebalance = create_rebalance(
            user_portfolio=signal_portfolio,
            type=RebalanceTypes.CASH_ALLOCATION.value,
        )
        service_rebalance = create_rebalance(
            user_portfolio=service_portfolio,
            type=RebalanceTypes.CASH_ALLOCATION.value,
        )

        signals.user_portfolio_rebalance_save(
            sender=UserPortfolioRebalance,
            instance=signal_rebalance,
            created=True,
        )
        apply_user_portfolio_rebalance_effects(
            service_rebalance,
            created=True,
        )

        signal_rebalance.refresh_from_db()
        service_rebalance.refresh_from_db()
        self.assertEqual(
            service_rebalance.rebalance_id,
            signal_rebalance.rebalance_id,
        )
