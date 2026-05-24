"""Basket save side-effects, decomposed into small methods.

The behaviour was originally a single ``post_save`` receiver at
``apps.portfolio.signals.user_basket_save``. Phase 1 step 2 of the
unification plan (§7.8) extracts it into a named service so subsequent
passes can route callers here and reduce the signal itself to a thin
adapter.

This module exposes two surfaces:

* ``apply_basket_effects(instance, *, created)`` — the public function.
  It is what callers import and what the (future) thin-adapter signal
  will invoke.
* ``BasketEffectsApplier`` — the worker class behind that function.
  One method per concern so the orchestration in ``apply()`` reads as a
  checklist and each branch can be unit-tested in isolation.

Bug-for-bug parity with the original signal is intentional. Any
divergence between this code and ``user_basket_save`` is a defect in
the extraction, not a deliberate fix. See the class docstring for the
list of known parity issues being carried forward unchanged.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from apps.portfolio.constants import OrderCurrentStatus
from apps.portfolio.models import Basket, Order

logger = logging.getLogger(__name__)


class BasketEffectsApplier:
    """Apply the side-effects of a Basket save in signal order.

    The orchestration in :meth:`apply` mirrors the original signal's
    control flow exactly:

    1. Log the entry banner and current-state details.
    2. For each row in ``user_allocation``: get or create the matching
       ``Order`` for ``basket`` and ``trading_symbol``.
    3. Copy ``stop_loss``, ``leverage`` and the SL-aware ``states``
       list onto each order, then save it.
    4. With no allocation: log the legacy no-op.

    Known parity issues (NOT fixed in this pass)
    --------------------------------------------
    * The ``created`` flag is accepted for signal parity but unused.
    * Saving each ``Order`` can still trigger legacy signal cascades
      once this service is wired. That routing is deferred.

    Caller contract
    ---------------
    Nothing calls this class or :func:`apply_basket_effects` in
    production yet. Both exist as the named contract that step-3
    callers and the step-4 thin-adapter signal will route through.
    """

    def __init__(
        self,
        instance: Basket,
        *,
        created: bool,
    ) -> None:
        """Bind the instance and create-flag this applier will act on."""
        self._instance = instance
        self._created = created

    def apply(self) -> None:
        """Run every side-effect in the original signal's order."""
        logger.info("Post User Basket Save Signal")
        logger.info(
            f"Current status of Basket {self._instance.id} is "
            f"{self._instance.current_state}"
        )

        if self._instance.user_allocation:
            self._process_allocation_rows()
        else:
            logger.info(
                "User allocation does not exists to create instructions."
            )

    def _process_allocation_rows(self) -> None:
        """Upsert one order per allocation row from the basket payload."""
        logger.info(
            f"Processing user allocation for Basket {self._instance.id}: "
            f"{self._instance.user_allocation}"
        )

        for order_data in self._instance.user_allocation:
            self._upsert_order_for_allocation(order_data)

    def _upsert_order_for_allocation(
        self,
        order_data: Mapping[str, Any],
    ) -> None:
        """Preserve legacy get-or-create behaviour and its log points."""
        trading_symbol = order_data.get("symbol")
        stop_loss = order_data.get("stop_loss")
        leverage = order_data.get("leverage")
        states = self._states_for(stop_loss)
        try:
            order = Order.objects.get(
                basket=self._instance,
                trading_symbol=trading_symbol,
            )
            order.stop_loss = stop_loss
            order.leverage = leverage
            order.states = states
            logger.info(
                f"Updating order for {trading_symbol} in Basket "
                f"{self._instance.id}"
            )
        except Order.DoesNotExist as exc:
            logger.info("Error while creating orders in user_basket_save.")
            order = Order(
                basket=self._instance,
                trading_symbol=trading_symbol,
                stop_loss=stop_loss,
                leverage=leverage,
                states=states,
            )
            logger.info(
                f"Creating new order for {trading_symbol} in Basket "
                f"{self._instance.id}"
            )

        order.save()
        logger.info(
            f"Order saved for {trading_symbol} in Basket {self._instance.id}"
        )

    @staticmethod
    def _states_for(stop_loss: Any) -> Any:
        """Select the legacy order-state list based on stop-loss truth."""
        return (
            OrderCurrentStatus.STATES_WITH_SL.value
            if stop_loss
            else OrderCurrentStatus.STATES_WITHOUT_SL.value
        )


def apply_basket_effects(
    instance: Basket,
    *,
    created: bool,
) -> None:
    """Apply Basket post-save side-effects.

    Thin facade around :class:`BasketEffectsApplier` so callers have a
    single function-shaped entry point matching the other
    ``apply_*_effects`` services in this package. The behaviour is
    bug-for-bug parity with
    ``apps.portfolio.signals.user_basket_save``; see the applier class
    docstring for the full behaviour and known parity issues.

    :param instance: The Basket whose save just happened.
    :param created: ``True`` when the save inserted a new row; mirrors
        the ``created`` kwarg Django passes to ``post_save`` receivers.
    """
    BasketEffectsApplier(instance, created=created).apply()
