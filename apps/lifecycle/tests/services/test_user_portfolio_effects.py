"""Tests for UserPortfolio side-effect extraction."""

from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase

from apps.lifecycle.services import apply_user_portfolio_effects
from apps.lifecycle.tests.utils import (
    LifecycleSignalIsolationMixin,
    create_user_portfolio,
)
from apps.portfolio import signals
from apps.portfolio.constants import ProductTypes
from apps.portfolio.models import UserPortfolio


class UserPortfolioEffectsTests(LifecycleSignalIsolationMixin, TestCase):
    """Verify extracted UserPortfolio save effects preserve parity."""

    @patch("apps.lifecycle.services.user_portfolio_effects.JobScheduler")
    def test_create_path_equity_calls_job_scheduler(
        self,
        scheduler: object,
    ) -> None:
        """Assert EQUITY creation dispatches the profile job."""
        portfolio = create_user_portfolio(
            product_type=ProductTypes.EQUITY.value,
        )

        apply_user_portfolio_effects(portfolio, created=True)

        scheduler.return_value.process_user_profile.assert_called_once_with(
            {"user_portfolio_ids": [portfolio.id]},
        )

    @patch("apps.lifecycle.services.user_portfolio_effects.JobScheduler")
    def test_update_path_equity_calls_job_scheduler(
        self,
        scheduler: object,
    ) -> None:
        """Assert EQUITY update also dispatches the profile job."""
        portfolio = create_user_portfolio(
            product_type=ProductTypes.EQUITY.value,
        )

        apply_user_portfolio_effects(portfolio, created=False)

        scheduler.return_value.process_user_profile.assert_called_once_with(
            {"user_portfolio_ids": [portfolio.id]},
        )

    @patch("apps.lifecycle.services.user_portfolio_effects.JobScheduler")
    def test_non_equity_is_noop(self, scheduler: object) -> None:
        """Assert non-EQUITY portfolio does not call the scheduler."""
        portfolio = create_user_portfolio(product_type=ProductTypes.MTF.value)

        apply_user_portfolio_effects(portfolio, created=False)

        scheduler.assert_not_called()

    @patch("apps.lifecycle.services.user_portfolio_effects.JobScheduler")
    @patch("apps.portfolio.signals.JobScheduler")
    def test_service_matches_signal_for_equity(
        self,
        signal_scheduler: object,
        service_scheduler: object,
    ) -> None:
        """Assert direct receiver and service call scheduler equally."""
        signal_portfolio = create_user_portfolio(user_id="signal")
        service_portfolio = create_user_portfolio(user_id="service")

        signals.user_portfolio_post_save(
            sender=UserPortfolio,
            instance=signal_portfolio,
            created=False,
        )
        apply_user_portfolio_effects(service_portfolio, created=False)

        signal_call = (
            signal_scheduler.return_value
            .process_user_profile
            .call_args
            .args[0]
        )
        service_call = (
            service_scheduler.return_value
            .process_user_profile
            .call_args
            .args[0]
        )
        self.assertEqual(
            service_call["user_portfolio_ids"][0],
            service_portfolio.id,
        )
        self.assertEqual(
            len(signal_call["user_portfolio_ids"]),
            len(service_call["user_portfolio_ids"]),
        )
