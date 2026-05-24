"""Convert a completed rebalance into basket monitoring records.

Service layer that converts a *completed* ``UserPortfolioRebalance`` into a
live :class:`~apps.portfolio.models.Basket` and boot-straps all dependent
:class:`~apps.portfolio.models.Order` and
:class:`~apps.portfolio.models.OrderInstruction` rows.

**Currently not wired** - there is no caller. The unification plan section
7.8 specifies this function will be invoked as an explicit transition hook
from ``TransitionService._schedule_side_effects`` when
``UserPortfolioRebalance`` transitions to ``complete``. That wiring lands in
a later Phase 1 pass.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from django.db import transaction

from apps.portfolio.constants import BasketStates, Side, OrderInstructionSources
from apps.portfolio.models import (
    Basket,
    Order,
    UserPortfolioRebalance,
    PortfolioRebalanceTransaction,
)
from apps.portfolio.services.basket import create_basket
from apps.portfolio.services.order_instructions import create_order_instructions

logger = logging.getLogger(__name__)

__all__ = [
    "create_basket_from_rebalance",
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _flatten_allocations(upr: UserPortfolioRebalance) -> List[Dict[str, Any]]:
    """
    Flatten allocation_quantity from all PortfolioRebalanceTransaction records
    for the given rebalance, ensuring each entry has a leverage key (default 1.0).
    """
    allocations: List[Dict[str, Any]] = []
    prts = PortfolioRebalanceTransaction.objects.filter(portfolio_rebalance=upr)
    for prt in prts:
        for alloc in prt.allocation_quantity or []:
            item = alloc.copy()
            item["leverage"] = item.get("leverage", 1.0)
            allocations.append(item)
    return allocations



# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

@transaction.atomic
def create_basket_from_rebalance(upr: UserPortfolioRebalance) -> Optional[Basket]:
    """Bootstrap monitoring Basket + children when *upr* reaches **complete**."""

    logger.info("[rebalance_to_basket] Creating basket from UserPortfolioRebalance %s", upr.id)

    allocations = _flatten_allocations(upr)
    if not allocations:
        logger.warning("No allocations found for UserPortfolioRebalance %s – skipping basket creation", upr.id)
        return None

    up = upr.user_portfolio

    # --- Basket ------------------------------------------------------------
    basket_data: Dict[str, Any] = {
        "user_id": up.user_id,
        "current_state": BasketStates.MONITORING.value,
        "broker": up.broker,
        "model_id": up.portfolio_id,
        "payment_id": up.subscription_id,
        "recommendation_id": upr.id,  # traceability link
        "product_type": up.product_type,
        "basket_type": "normal",
        "user_allocation": allocations
    }

    basket = create_basket(basket_data)
    logger.info("Created Basket %s from rebalance %s", basket.id, upr.id)

    # --- Orders ------------------------------------------------------------
    symbol_to_order: Dict[str, Order] = {}
    for alloc in allocations:
        order = Order.objects.create(
            basket=basket,
            trading_symbol=alloc["symbol"],
            leverage=alloc.get("leverage", 1.0),
            stop_loss=alloc.get("stop_loss"),
        )
        symbol_to_order[alloc["symbol"]] = order

    # --- OrderInstructions (BUY only at start) -----------------------------
    instruction_payload = [
        {
            "order_id": symbol_to_order[alloc["symbol"]].id,
            "symbol": alloc["symbol"],
            "quantity": alloc["quantity"],
            "side": Side.BUY.value,
            "source": OrderInstructionSources.MANUAL.value,
        }
        for alloc in allocations
    ]
    create_order_instructions(instruction_payload)

    logger.info("Basket %s bootstrapped with %d orders & instructions", basket.id, len(instruction_payload))
    return basket
