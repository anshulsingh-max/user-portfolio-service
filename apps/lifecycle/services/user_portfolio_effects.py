"""UserPortfolio save side-effects, decomposed into small methods.

The behaviour was originally a single ``post_save`` receiver at
``apps.portfolio.signals.user_portfolio_post_save``. Phase 1 step 2 of
the unification plan (§7.8) extracts it into a named service so
subsequent passes can route callers here and reduce the signal itself
to a thin adapter.

This module exposes two surfaces:

* ``apply_user_portfolio_effects(instance, *, created)`` — the public
  function. It is what callers import and what the (future)
  thin-adapter signal will invoke.
* ``UserPortfolioEffectsApplier`` — the worker class behind that
  function. One method per concern so the orchestration in ``apply()``
  reads as a checklist and each branch can be unit-tested in isolation.

Bug-for-bug parity with the original signal is intentional. Any
divergence between this code and ``user_portfolio_post_save`` is a
defect in the extraction, not a deliberate fix. See the class docstring
for the list of known parity issues being carried forward unchanged.
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

from apps.portfolio.constants import ProductTypes
from apps.portfolio.models import UserPortfolio
from bw_essentials.services.job_scheduler import JobScheduler

logger = logging.getLogger(__name__)


class UserPortfolioEffectsApplier:
    """Apply the side-effects of a UserPortfolio save in signal order.

    The orchestration in :meth:`apply` mirrors the original signal's
    control flow exactly:

    1. Log the entry banner.
    2. For EQUITY portfolios on any save: call
       ``JobScheduler(APP_NAME, broker).process_user_profile`` with the
       saved portfolio id.
    3. Wrap the external call in the legacy broad ``try``/``except``.
    4. For other product types: no-op.

    Known parity issues (NOT fixed in this pass)
    --------------------------------------------
    * The ``created`` flag is accepted for signal parity but unused.
    * The broad exception handler is preserved for parity.

    Caller contract
    ---------------
    Nothing calls this class or :func:`apply_user_portfolio_effects` in
    production yet. Both exist as the named contract that step-3
    callers and the step-4 thin-adapter signal will route through.
    """

    def __init__(
        self,
        instance: UserPortfolio,
        *,
        created: bool,
    ) -> None:
        """Bind the instance and create-flag this applier will act on."""
        self._instance = instance
        self._created = created

    def apply(self) -> None:
        """Run every side-effect in the original signal's order."""
        instance = self._instance
        logger.info(
            f"In post_save for UserPortfolio, {instance.product_type=}"
        )
        try:
            self._dispatch_job_scheduler_for_equity()
        except Exception as e:
            logger.exception(
                f"Failed to call API for UserPortfolio "
                f"{self._instance.id}: {e}"
            )

    def _dispatch_job_scheduler_for_equity(self) -> None:
        """Call the legacy scheduler only for EQUITY portfolios."""
        if self._instance.product_type == ProductTypes.EQUITY.value:
            tenant_id = self._instance.broker
            data: dict[str, Any] = {
                "user_portfolio_ids": [self._instance.id],
            }
            JobScheduler(settings.APP_NAME, tenant_id).process_user_profile(
                data,
            )


def apply_user_portfolio_effects(
    instance: UserPortfolio,
    *,
    created: bool,
) -> None:
    """Apply UserPortfolio post-save side-effects.

    Thin facade around :class:`UserPortfolioEffectsApplier` so callers
    have a single function-shaped entry point matching the other
    ``apply_*_effects`` services in this package. The behaviour is
    bug-for-bug parity with
    ``apps.portfolio.signals.user_portfolio_post_save``; see the
    applier class docstring for the full behaviour and known parity
    issues.

    :param instance: The UserPortfolio whose save just happened.
    :param created: ``True`` when the save inserted a new row; mirrors
        the ``created`` kwarg Django passes to ``post_save`` receivers.
    """
    UserPortfolioEffectsApplier(instance, created=created).apply()
