"""OrderInstruction save side-effects, decomposed into small methods.

The behaviour was originally a single ``post_save`` receiver at
``apps.portfolio.signals.order_instruction_save``. Phase 1 step 2 of
the unification plan (§7.8) extracts it into a named service so
subsequent passes can route API / callback / task / admin call sites
here and reduce the legacy signal to a thin adapter.

This module exposes two surfaces:

* ``apply_order_instruction_effects(instance, *, created)`` — the
  public function. It is what callers import and what the (future)
  thin-adapter signal will invoke.
* ``OrderInstructionEffectsApplier`` — the worker class behind that
  function. One method per concern so the orchestration in ``apply()``
  reads as a checklist and each branch can be unit-tested in isolation.

Bug-for-bug parity with the original signal is intentional. The
infamous B3 doubled cascade — two consecutive ``order.save()`` calls
in the FILLED branch, each of which re-fires ``orders_save`` — is
preserved deliberately so the parity window stays meaningful.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db.models.aggregates import Sum

from apps.portfolio.constants import OrderStatus, Side
from apps.portfolio.models import Order, OrderInstruction
from apps.portfolio.services.orders import get_next_order_state

logger = logging.getLogger(__name__)


class OrderInstructionEffectsApplier:
    """Apply the side-effects of an OrderInstruction save in signal order.

    The orchestration in :meth:`apply` mirrors the original signal's
    control flow exactly:

    1. Log the entry banner.
    2. Defensively re-fetch the parent ``Order`` by id so the row
       reflects whatever the in-flight transaction has already
       written (the original signal uses
       ``Order.objects.get(id=instance.order.id)`` rather than
       ``instance.order`` for the same reason).
    3. On create: advance ``order.current_status`` via
       ``get_next_order_state`` and save the order. This re-fires
       ``orders_save`` (B3 cascade) and that is intentional in this
       pass.
    4. On a FILLED instruction: stamp ``{side}_price`` on the order,
       recompute ``initial_amount`` (BUY fill sum) and ``end_amount``
       (SELL fill sum), advance the state again, and save again.
       That is a SECOND re-fire of ``orders_save`` — also intentional.

    Known parity issues (NOT fixed in this pass)
    --------------------------------------------
    * **B3** — both ``order.save()`` call sites are preserved, so a
      single FILLED instruction save can re-trigger ``orders_save``
      twice in a row. Folding the two writes into one or routing them
      through ``TransitionService.transition`` is deferred so the
      parity window stays meaningful.
    * Direct writes to ``order.current_status`` are preserved at both
      sites for the same reason. Each is flagged with a
      ``# TODO(phase1-step3)`` marker in the helper methods.

    Caller contract
    ---------------
    Nothing calls this class or
    :func:`apply_order_instruction_effects` in production yet. Both
    exist as the named contract that step-3 callers and the step-4
    thin-adapter signal will route through.
    """

    def __init__(
        self,
        instance: OrderInstruction,
        *,
        created: bool,
    ) -> None:
        """Bind the instance and create-flag this applier will act on.

        :param instance: The OrderInstruction whose save just happened.
        :param created: ``True`` when the save inserted a new row;
            mirrors the ``created`` kwarg Django passes to
            ``post_save`` receivers.
        """
        self._instance = instance
        self._created = created

    def apply(self) -> None:
        """Run every side-effect in the original signal's order.

        The method is intentionally a thin orchestrator — each step is
        delegated to a named helper so the control flow reads as a
        checklist and individual branches can be tested in isolation.
        """
        logger.info("Post Order Instructions Save Signal")
        logger.info(
            f"Current status of OrderInstruction {self._instance.id} "
            f"is {self._instance.status}"
        )

        order = self._load_order()

        if self._created:
            self._advance_order_state_on_create(order)

        if self._instance.status == OrderStatus.FILLED.value:
            self._settle_filled_amounts(order)

    def _load_order(self) -> Order:
        """Defensively re-fetch the parent ``Order`` from the DB.

        The original signal used ``Order.objects.get(id=instance.order.id)``
        rather than ``self._instance.order`` so the row reflects any
        in-flight writes the current transaction has already applied
        to the parent. Preserved verbatim.
        """
        return Order.objects.get(id=self._instance.order.id)

    def _advance_order_state_on_create(self, order: Order) -> None:
        """Set ``current_status`` from ``get_next_order_state`` and save.

        The original on-create branch advances the parent order's
        lifecycle status as soon as a child instruction is created.
        The ``order.save()`` re-fires ``orders_save`` — the first
        edge of the B3 cascade — which is preserved on purpose.
        """
        logger.info(f"{self._created =}, updating order current state.")
        # TODO(phase1-step3): route via TransitionService.transition()
        order.current_status = get_next_order_state(self._instance)
        order.save()

    def _settle_filled_amounts(self, order: Order) -> None:
        """Stamp price, recompute amounts, advance state, save again.

        Runs only for FILLED instructions. Stamps the side-specific
        price column on the order, recomputes ``initial_amount`` /
        ``end_amount`` from the current FILLED-row aggregates, then
        advances the lifecycle status and saves the order — the
        second edge of the B3 cascade. All three writes are bundled
        into one ``save()`` so the on-disk row is internally consistent
        when the cascade re-fires.
        """
        self._record_side_price(order)
        order.initial_amount = self._compute_side_total(order, Side.BUY.value)
        order.end_amount = self._compute_side_total(order, Side.SELL.value)

        # TODO(phase1-step3): route via TransitionService.transition()
        order.current_status = get_next_order_state(self._instance)
        order.save()

        logger.info(
            f"Order {order.id} updated with {self._instance.side}_price: "
            f"{self._instance.order_price}, amount: initial_amount: "
            f"{order.initial_amount}, end_amount: {order.end_amount}"
        )

    def _record_side_price(self, order: Order) -> None:
        """Stamp ``{buy,sell}_price`` on the order from the instruction.

        Uses ``setattr`` so a BUY instruction writes ``buy_price`` and
        a SELL writes ``sell_price``. The original signal relied on
        the same dynamic attribute write — preserved unchanged.
        """
        setattr(
            order,
            f"{self._instance.side}_price",
            self._instance.order_price,
        )

    def _compute_side_total(self, order: Order, side: str) -> Any:
        """Return the sum of ``value`` over FILLED rows for one side.

        ``None`` from ``aggregate`` is normalised to ``0`` so the
        downstream attribute assignment never writes ``None`` into a
        numeric column. The return type is ``Any`` because the sum
        comes back as a ``Decimal`` from the ORM but the fallback is
        a plain ``int`` — both are accepted by the model field.
        """
        total = (
            OrderInstruction.objects.filter(
                order=order,
                side=side,
                status=OrderStatus.FILLED.value,
            )
            .aggregate(total=Sum("value"))
            .get("total")
        )
        return total or 0


def apply_order_instruction_effects(
    instance: OrderInstruction,
    *,
    created: bool,
) -> None:
    """Apply OrderInstruction post-save side-effects.

    Thin facade around :class:`OrderInstructionEffectsApplier` so
    callers have a single function-shaped entry point matching the
    other ``apply_*_effects`` services in this package. The behaviour
    is bug-for-bug parity with
    ``apps.portfolio.signals.order_instruction_save``; see the applier
    class docstring for the full behaviour and known parity issues.

    :param instance: The OrderInstruction whose save just happened.
    :param created: ``True`` when the save inserted a new row; mirrors
        the ``created`` kwarg Django passes to ``post_save`` receivers.
    """
    OrderInstructionEffectsApplier(instance, created=created).apply()
