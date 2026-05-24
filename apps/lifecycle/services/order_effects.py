"""Order save side-effects, decomposed into small methods.

The behaviour was originally a single ``post_save`` receiver at
``apps.portfolio.signals.orders_save``. Phase 1 step 2 of the
unification plan (§7.8) extracts it into a named service so subsequent
passes can route callers here and reduce the signal itself to a thin
adapter.

This module exposes two surfaces:

* ``apply_order_effects(instance, *, created)`` — the public function.
  It is what callers import and what the (future) thin-adapter signal
  will invoke.
* ``OrderEffectsApplier`` — the worker class behind that function. One
  method per concern so the orchestration in ``apply()`` reads as a
  checklist and each branch can be unit-tested in isolation.

Bug-for-bug parity with the original signal is intentional. Any
divergence between this code and ``orders_save`` is a defect in the
extraction, not a deliberate fix. See the class docstring for the list
of known parity issues being carried forward unchanged.
"""

from __future__ import annotations

import logging

from apps.portfolio.constants import OrderCurrentStatus
from apps.portfolio.models import Order
from apps.portfolio.services.basket import update_basket_details
from apps.portfolio.services.order_instructions import create_instructions

logger = logging.getLogger(__name__)


class OrderEffectsApplier:
    """Apply the side-effects of an Order save in signal order.

    The orchestration in :meth:`apply` mirrors the original signal's
    control flow exactly:

    1. Log the entry banner and current-status details.
    2. On create: create ``OrderInstruction`` rows from basket
       allocation.
    3. When status is BUY, SELL, or SKIP: update basket totals and
       current state through the existing basket service.

    Known parity issues (NOT fixed in this pass)
    --------------------------------------------
    * Direct basket state writes still happen inside the called legacy
      service. Routing through ``TransitionService.transition`` is
      deferred.

    Caller contract
    ---------------
    Nothing calls this class or :func:`apply_order_effects` in
    production yet. Both exist as the named contract that step-3
    callers and the step-4 thin-adapter signal will route through.
    """

    def __init__(
        self,
        instance: Order,
        *,
        created: bool,
    ) -> None:
        """Bind the instance and create-flag this applier will act on."""
        self._instance = instance
        self._created = created

    def apply(self) -> None:
        """Run every side-effect in the original signal's order."""
        logger.info("Post Orders Save Signal")
        logger.info(
            f"Current status of Order {self._instance.id} is "
            f"{self._instance.current_status}"
        )

        self._create_instructions_on_create()
        self._refresh_basket_on_terminal_status()

    def _create_instructions_on_create(self) -> None:
        """Create child instructions only for newly inserted orders."""
        if self._created:
            create_instructions(self._instance)

    def _refresh_basket_on_terminal_status(self) -> None:
        """Refresh basket rollups for statuses the legacy signal handled."""
        if self._instance.current_status in [
            OrderCurrentStatus.BUY.value,
            OrderCurrentStatus.SELL.value,
            OrderCurrentStatus.SKIP.value,
        ]:
            update_basket_details(self._instance)


def apply_order_effects(
    instance: Order,
    *,
    created: bool,
) -> None:
    """Apply Order post-save side-effects.

    Thin facade around :class:`OrderEffectsApplier` so callers have a
    single function-shaped entry point matching the other
    ``apply_*_effects`` services in this package. The behaviour is
    bug-for-bug parity with ``apps.portfolio.signals.orders_save``; see
    the applier class docstring for the full behaviour and known parity
    issues.

    :param instance: The Order whose save just happened.
    :param created: ``True`` when the save inserted a new row; mirrors
        the ``created`` kwarg Django passes to ``post_save`` receivers.
    """
    OrderEffectsApplier(instance, created=created).apply()
