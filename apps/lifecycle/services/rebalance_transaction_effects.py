"""PortfolioRebalanceTransaction save side-effects, decomposed.

The behaviour was originally a single ``post_save`` receiver at
``apps.portfolio.signals.rebalance_transaction_save``. Phase 1 step 2
of the unification plan (§7.8) extracts it into a named service so
subsequent passes can route callers here and reduce the signal itself
to a thin adapter.

This module exposes two surfaces:

* ``apply_rebalance_transaction_effects(instance, *, created)`` — the
  public function. It is what callers import and what the (future)
  thin-adapter signal will invoke.
* ``RebalanceTransactionEffectsApplier`` — the worker class behind that
  function. One method per concern so the orchestration in ``apply()``
  reads as a checklist and each branch can be unit-tested in isolation.

Bug-for-bug parity with the original signal is intentional. Any
divergence between this code and ``rebalance_transaction_save`` is a
defect in the extraction, not a deliberate fix. See the class docstring
for the list of known parity issues being carried forward unchanged.
"""

from __future__ import annotations

import logging

from apps.portfolio.constants import RebalanceTransactionStates
from apps.portfolio.models import PortfolioRebalanceTransaction
from apps.portfolio.services.user_instruction import create_user_instruction
from apps.portfolio.services.user_portfolio_rebalance import (
    update_rebalance_state,
)

logger = logging.getLogger(__name__)


class RebalanceTransactionEffectsApplier:
    """Apply side-effects of a PortfolioRebalanceTransaction save.

    The orchestration in :meth:`apply` mirrors the original signal's
    control flow exactly:

    1. Log the entry banner and current-state details.
    2. On create: call ``create_user_instruction(instance.id)``.
    3. On a completion state: update the parent
       ``UserPortfolioRebalance`` via the existing service.

    Known parity issues (NOT fixed in this pass)
    --------------------------------------------
    * Direct state writes still happen inside the called legacy service.
      Routing through ``TransitionService.transition`` is deferred.

    Caller contract
    ---------------
    Nothing calls this class or
    :func:`apply_rebalance_transaction_effects` in production yet. Both
    exist as the named contract that step-3 callers and the step-4
    thin-adapter signal will route through.
    """

    def __init__(
        self,
        instance: PortfolioRebalanceTransaction,
        *,
        created: bool,
    ) -> None:
        """Bind the instance and create-flag this applier will act on."""
        self._instance = instance
        self._created = created

    def apply(self) -> None:
        """Run every side-effect in the original signal's order."""
        logger.info(
            f"Post Portfolio Rebalance Transaction save signal for "
            f"created={self._created}"
        )
        logger.info(
            f"Current status {self._instance.id} is "
            f"{self._instance.current_state} and product type is "
            f"{self._instance.portfolio_rebalance.user_portfolio.product_type}"
        )

        self._create_instructions_on_create()
        self._propagate_completion_state()

    def _create_instructions_on_create(self) -> None:
        """Create child instructions only for newly inserted PRT rows."""
        if self._created:
            create_user_instruction(self._instance.id)

    def _propagate_completion_state(self) -> None:
        """Push terminal transaction state up to the parent rebalance.

        The called legacy service owns the rollup semantics; this
        guard preserves the original signal's completion-only trigger.
        """
        if (
            self._instance.current_state
            in RebalanceTransactionStates.COMPLETION_STATES.value
        ):
            update_rebalance_state(
                self._instance.portfolio_rebalance,
                self._instance.current_state,
                self._instance.type,
            )


def apply_rebalance_transaction_effects(
    instance: PortfolioRebalanceTransaction,
    *,
    created: bool,
) -> None:
    """Apply PortfolioRebalanceTransaction post-save side-effects.

    Thin facade around :class:`RebalanceTransactionEffectsApplier` so
    callers have a single function-shaped entry point matching the
    other ``apply_*_effects`` services in this package. The behaviour
    is bug-for-bug parity with
    ``apps.portfolio.signals.rebalance_transaction_save``; see the
    applier class docstring for the full behaviour and known parity
    issues.

    :param instance: The PortfolioRebalanceTransaction whose save just
        happened.
    :param created: ``True`` when the save inserted a new row; mirrors
        the ``created`` kwarg Django passes to ``post_save`` receivers.
    """
    RebalanceTransactionEffectsApplier(instance, created=created).apply()
