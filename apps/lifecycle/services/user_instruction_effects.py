"""UserInstruction save side-effects, decomposed into small methods.

The behaviour was originally a single 170-line ``post_save`` receiver in
``apps.portfolio.signals.user_instructions_save``. Phase 1 step 2 of the
unification plan (§7.8) extracts it into a named service so subsequent
passes can route API / callback / task / admin call sites here and reduce
the legacy signal to a thin adapter.

This module exposes two surfaces:

* ``apply_user_instruction_effects(instance, *, created)`` — the public
  function. It is what callers import and what the (future) thin-adapter
  signal will invoke.
* ``UserInstructionEffectsApplier`` — the worker class behind that
  function. One method per concern so the orchestration in ``apply()``
  reads as a checklist and each branch can be unit-tested in isolation.

Bug-for-bug parity with the original signal is intentional. Any
divergence between this code and ``user_instructions_save`` is a defect
in the extraction, not a deliberate fix. See the class docstring for the
list of known parity issues being carried forward unchanged.
"""

from __future__ import annotations

import logging
from typing import Tuple

from django.db.models.aggregates import Sum

from apps.holdings.services.transaction import update_or_create_holding
from apps.portfolio.constants import Asset, OrderStatus, Side
from apps.portfolio.models import (
    PortfolioRebalanceTransaction,
    UserInstruction,
)
from apps.portfolio.serializers.portfolio_rebalance_transaction import (
    PortfolioRebalanceTransactionUpdateSerializer,
)
from apps.portfolio.services.rebalance_transaction import (
    refresh_portfolio_rebalance_transaction,
)
from apps.portfolio.tasks import phase_detail_callback
from multitenant.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class UserInstructionEffectsApplier:
    """Apply the side-effects of a UserInstruction save in signal order.

    The orchestration in :meth:`apply` mirrors the original signal's
    control flow exactly:

    1. Log the entry banner (two lines, as the signal did).
    2. On create: stamp ``order_tag = instance.id`` without re-firing
       save signals (uses ``.update()``).
    3. On a terminal ``status`` (``OrderStatus.COMPLETED_STATES``):
       FILLED rows update holdings, refresh the parent PRT, and — for
       SELL fills — enqueue ``phase_detail_callback``. Non-FILLED
       terminal rows only refresh the PRT.
    4. Always: re-read the PRT, aggregate filled instructions, and
       write ``executed_list`` / ``amount`` back through
       ``PortfolioRebalanceTransactionUpdateSerializer``.

    Known parity issues (NOT fixed in this pass)
    --------------------------------------------
    * **B4** — the original receiver mixes holdings updates, async
      task dispatch, serializer writes, and aggregations in one
      function. The class decomposition splits the *code* but
      preserves the *behaviour*; decomposition into separate services
      with cleaner transaction boundaries is deferred so the parity
      window stays meaningful.
    * Direct ``current_state`` writes inside the legacy services this
      class calls (``refresh_portfolio_rebalance_transaction`` etc.)
      are NOT yet routed through ``TransitionService.transition``.
      That routing lands in a later Phase 1 pass.

    Caller contract
    ---------------
    Nothing calls this class or :func:`apply_user_instruction_effects`
    in production yet. Both exist as the named contract that step-3
    callers and the step-4 thin-adapter signal will route through.
    """

    def __init__(
        self,
        instance: UserInstruction,
        *,
        created: bool,
    ) -> None:
        """Bind the instance and create-flag this applier will act on.

        :param instance: The UserInstruction whose save just happened.
        :param created: ``True`` when the save inserted a new row;
            mirrors the ``created`` kwarg Django passes to ``post_save``
            receivers.
        """
        self._instance = instance
        self._created = created

    def apply(self) -> None:
        """Run every side-effect in the original signal's order.

        The method is intentionally a thin orchestrator — each step is
        delegated to a named helper so the control flow reads as a
        checklist and individual branches can be tested in isolation.
        """
        logger.info("Post UserInstruction save signal")
        logger.info(
            f"Current status {self._instance.id} is {self._instance.status}"
        )

        if self._created:
            self._stamp_order_tag()

        if self._instance.status in OrderStatus.COMPLETED_STATES.value:
            self._handle_completed_status()

        self._aggregate_and_persist_summary()

    def _stamp_order_tag(self) -> None:
        """Set ``order_tag = id`` on the row without re-firing signals.

        Uses ``QuerySet.update`` (not ``instance.save``) so this side-
        effect does not recursively trigger ``post_save``. The tenant
        is read and logged purely for traceability; it does not
        participate in the write.
        """
        tenant_id = get_current_tenant()
        order_tag = self._instance.id
        UserInstruction.objects.filter(id=self._instance.id).update(
            order_tag=order_tag,
        )
        logger.info(
            f"Set order_tag for UserInstruction {self._instance.id} "
            f"to {order_tag} (tenant={tenant_id})"
        )

    def _handle_completed_status(self) -> None:
        """Branch on status: FILLED rows do the heavy work, others refresh.

        Non-FILLED terminal statuses (CANCEL, FAILED) only nudge the
        parent PRT to recompute its rollup state — there are no
        holdings to settle and no callback to dispatch.
        """
        prt = self._instance.portfolio_rebalance_transaction
        logger.info(
            f"UserInstruction {self._instance.id} moved to completed "
            f"state {self._instance.status}; evaluating "
            f"PortfolioRebalanceTransaction {prt.id}"
        )

        if self._instance.status == OrderStatus.FILLED.value:
            self._process_filled(prt)
        else:
            refresh_portfolio_rebalance_transaction(prt)

    def _process_filled(
        self,
        prt: PortfolioRebalanceTransaction,
    ) -> None:
        """Settle holdings for a FILLED instruction and refresh the PRT.

        Performs two ``update_or_create_holding`` calls — one for the
        symbol leg, one for cash — then refreshes the owning PRT. If
        the fill is a SELL, also enqueues ``phase_detail_callback`` so
        the buy-after-sell phase handoff is scheduled.
        """
        user_portfolio_id = prt.portfolio_rebalance.user_portfolio
        cash_delta, symbol_quantity, price = self._compute_fill_deltas()

        logger.info(
            f"Processing FILLED instruction {self._instance.id}: "
            f"side={self._instance.side}, "
            f"symbol={self._instance.symbol}, "
            f"qty_filled={self._instance.filled_quantity}, "
            f"value={self._instance.value}, price={price}, "
            f"user_portfolio={user_portfolio_id}"
        )

        update_or_create_holding(
            user_portfolio_id,
            self._instance.symbol,
            symbol_quantity,
            price,
        )
        update_or_create_holding(
            user_portfolio_id,
            Asset.CASH.value,
            cash_delta,
            Asset.CASH_PRICE.value,
        )
        refresh_portfolio_rebalance_transaction(prt)

        if self._instance.side == Side.SELL.value:
            self._enqueue_phase_callback(prt)

    def _compute_fill_deltas(self) -> Tuple[float, float, float]:
        """Return ``(cash_delta, symbol_quantity, price)`` for this fill.

        BUY fills consume cash (negative cash_delta) and add to the
        symbol position; SELL fills release cash (positive cash_delta)
        and remove from the symbol position. SELL ``price`` is recorded
        as ``0`` here because the cash-side row carries the full
        proceeds — preserving the original signal's behaviour even
        though it is asymmetric.
        """
        inst = self._instance
        is_buy = inst.side == Side.BUY.value
        is_sell = inst.side == Side.SELL.value

        cash_delta = -1 * inst.value if is_buy else inst.value
        symbol_quantity = (
            inst.filled_quantity if is_buy else -1 * inst.filled_quantity
        )
        price = 0 if is_sell else inst.value / inst.quantity
        return cash_delta, symbol_quantity, price

    def _enqueue_phase_callback(
        self,
        prt: PortfolioRebalanceTransaction,
    ) -> None:
        """Dispatch the SELL-fill phase detail callback to Celery.

        The original signal re-reads the tenant id immediately before
        the dispatch — preserved here so the callback sees the same
        tenant context as the receiver did, even if other code in the
        request flipped it between the entry log and this line.
        """
        logger.info("Calling phase detail callback")
        tenant_id = get_current_tenant()
        phase_detail_callback.delay(
            prt.portfolio_rebalance.id,
            tenant_id=tenant_id,
            rebalance_transaction_id=prt.id,
        )

    def _aggregate_and_persist_summary(self) -> None:
        """Aggregate filled instructions and persist them to the PRT.

        Runs on every invocation — including non-terminal saves — so
        the PRT's rollup view always reflects the latest filled set.
        The re-read + ``refresh_from_db`` mirrors the original signal
        so any mutation that ``refresh_portfolio_rebalance_transaction``
        applied above is observed before the serializer write.
        """
        prt = self._instance.portfolio_rebalance_transaction
        prt.refresh_from_db()

        filled_orders = UserInstruction.objects.filter(
            portfolio_rebalance_transaction=prt,
            status=OrderStatus.FILLED.value,
        )
        executed_list = list(filled_orders.values_list("symbol", flat=True))
        amount = filled_orders.aggregate(total=Sum("value"))["total"] or 0
        updated_data = {
            "executed_list": executed_list,
            "amount": amount,
        }

        logger.info(
            f"Aggregated filled orders for PRT {prt.id}: "
            f"executed_list={executed_list}, amount={amount}"
        )
        serializer = PortfolioRebalanceTransactionUpdateSerializer(
            prt,
            data=updated_data,
        )
        logger.info(
            f"Initialized PortfolioRebalanceTransactionUpdateSerializer "
            f"for transaction {prt.id} with data={updated_data} and "
            f"{prt.current_state = }"
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            logger.info(
                f"Updated PortfolioRebalanceTransaction {prt.id} with "
                f"executed_list and amount"
            )


def apply_user_instruction_effects(
    instance: UserInstruction,
    *,
    created: bool,
) -> None:
    """Apply UserInstruction post-save side-effects.

    Thin facade around :class:`UserInstructionEffectsApplier` so callers
    have a single function-shaped entry point matching the other
    ``apply_*_effects`` services in this package. The behaviour is
    bug-for-bug parity with
    ``apps.portfolio.signals.user_instructions_save``; see the applier
    class docstring for the full behaviour and known parity issues.

    :param instance: The UserInstruction whose save just happened.
    :param created: ``True`` when the save inserted a new row; mirrors
        the ``created`` kwarg Django passes to ``post_save`` receivers.
    """
    UserInstructionEffectsApplier(instance, created=created).apply()
