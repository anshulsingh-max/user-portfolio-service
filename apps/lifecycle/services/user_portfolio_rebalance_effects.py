"""UserPortfolioRebalance save side-effects, decomposed.

The behaviour was originally a single ``post_save`` receiver at
``apps.portfolio.signals.user_portfolio_rebalance_save``. Phase 1 step
2 of the unification plan (§7.8) extracts it into a named service so
subsequent passes can route callers here and reduce the signal itself
to a thin adapter.

This module exposes two surfaces:

* ``apply_user_portfolio_rebalance_effects(instance, *, created)`` —
  the public function. It is what callers import and what the (future)
  thin-adapter signal will invoke.
* ``UserPortfolioRebalanceEffectsApplier`` — the worker class behind
  that function. One method per concern so the orchestration in
  ``apply()`` reads as a checklist and each branch can be unit-tested
  in isolation.

Bug-for-bug parity with the original signal is intentional. Any
divergence between this code and ``user_portfolio_rebalance_save`` is a
defect in the extraction, not a deliberate fix. See the class docstring
for the list of known parity issues being carried forward unchanged.
"""

from __future__ import annotations

import logging

from apps.portfolio.constants import RebalanceTypes
from apps.portfolio.models import UserPortfolioRebalance

logger = logging.getLogger(__name__)


class UserPortfolioRebalanceEffectsApplier:
    """Apply the side-effects of a UserPortfolioRebalance save.

    The orchestration in :meth:`apply` mirrors the original signal's
    control flow exactly:

    1. Log the entry banner.
    2. On create for ``cash_allocation``: copy ``rebalance_id`` from
       the last prior rebalance for the same user portfolio.
    3. If there is no prior rebalance: log the legacy warning and
       leave the row unchanged.
    4. On update or non-cash-allocation type: no-op.

    Known parity issues (NOT fixed in this pass)
    --------------------------------------------
    * None beyond preserving the legacy direct queryset update.

    Caller contract
    ---------------
    Nothing calls this class or
    :func:`apply_user_portfolio_rebalance_effects` in production yet.
    Both exist as the named contract that step-3 callers and the step-4
    thin-adapter signal will route through.
    """

    def __init__(
        self,
        instance: UserPortfolioRebalance,
        *,
        created: bool,
    ) -> None:
        """Bind the instance and create-flag this applier will act on."""
        self._instance = instance
        self._created = created

    def apply(self) -> None:
        """Run every side-effect in the original signal's order."""
        logger.info("Post User Portfolio Rebalance Save Signal")

        if not (
            self._created
            and self._instance.type == RebalanceTypes.CASH_ALLOCATION.value
        ):
            return

        self._copy_rebalance_id_from_prior()

    def _copy_rebalance_id_from_prior(self) -> None:
        """Copy the prior rebalance id through the legacy queryset update."""
        last_user_portfolio_rebalance = self._last_prior_rebalance()

        if last_user_portfolio_rebalance:
            UserPortfolioRebalance.objects.filter(
                id=self._instance.id,
            ).update(
                rebalance_id=last_user_portfolio_rebalance.rebalance_id,
            )
            logger.info(
                f"Updated rebalance_id for Order {self._instance.id} to "
                f"{last_user_portfolio_rebalance.rebalance_id}"
            )
        else:
            logger.warning(
                f"No previous UserPortfolioRebalance found for user "
                f"portfolio {self._instance.user_portfolio.id}"
            )

    def _last_prior_rebalance(self) -> UserPortfolioRebalance | None:
        """Return the most recent same-portfolio row before this row."""
        return (
            UserPortfolioRebalance.objects.filter(
                user_portfolio=self._instance.user_portfolio,
            )
            .exclude(id=self._instance.id)
            .order_by("-id")
            .first()
        )


def apply_user_portfolio_rebalance_effects(
    instance: UserPortfolioRebalance,
    *,
    created: bool,
) -> None:
    """Apply UserPortfolioRebalance post-save side-effects.

    Thin facade around :class:`UserPortfolioRebalanceEffectsApplier` so
    callers have a single function-shaped entry point matching the
    other ``apply_*_effects`` services in this package. The behaviour
    is bug-for-bug parity with
    ``apps.portfolio.signals.user_portfolio_rebalance_save``; see the
    applier class docstring for the full behaviour and known parity
    issues.

    :param instance: The UserPortfolioRebalance whose save just
        happened.
    :param created: ``True`` when the save inserted a new row; mirrors
        the ``created`` kwarg Django passes to ``post_save`` receivers.
    """
    UserPortfolioRebalanceEffectsApplier(
        instance,
        created=created,
    ).apply()
