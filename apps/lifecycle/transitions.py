"""Allowed lifecycle transitions for the Phase 1 authority.

The matrix is deliberately explicit so reporting and validation never infer
equivalence between similarly named states in different legacy flows.
"""

from __future__ import annotations

from apps.lifecycle.constants import CallbackStageType
from apps.portfolio.constants import (
    BasketStates,
    OrderCurrentStatus,
    RebalanceTransactionStates,
    States,
)


INITIAL_STATES: dict[str, str] = {
    CallbackStageType.REBALANCE_EVENT.value: States.PENDING.value,
    CallbackStageType.PHASE.value: RebalanceTransactionStates.PROCESSING.value,
    CallbackStageType.ORDER.value: OrderCurrentStatus.WAITING.value,
    CallbackStageType.BASKET.value: BasketStates.UNINVESTED.value,
}

ALLOWED: dict[str, dict[str, list[str]]] = {
    CallbackStageType.REBALANCE_EVENT.value: {
        States.PENDING.value: [
            States.PARTIAL.value,
            States.COMPLETE.value,
        ],
        States.PARTIAL.value: [States.COMPLETE.value],
        States.COMPLETE.value: [],
    },
    CallbackStageType.PHASE.value: {
        RebalanceTransactionStates.PROCESSING.value: [
            RebalanceTransactionStates.PARTIALLY_COMPLETED.value,
            RebalanceTransactionStates.COMPLETED.value,
            RebalanceTransactionStates.RETRY_ENABLED.value,
            RebalanceTransactionStates.MANUALLY_COMPLETED.value,
            RebalanceTransactionStates.SKIPPED.value,
        ],
        RebalanceTransactionStates.PARTIALLY_COMPLETED.value: [
            RebalanceTransactionStates.COMPLETED.value,
            RebalanceTransactionStates.RETRY_ENABLED.value,
            RebalanceTransactionStates.MANUALLY_COMPLETED.value,
        ],
        RebalanceTransactionStates.RETRY_ENABLED.value: [
            RebalanceTransactionStates.PROCESSING.value,
            RebalanceTransactionStates.COMPLETED.value,
            RebalanceTransactionStates.PARTIALLY_COMPLETED.value,
            RebalanceTransactionStates.MANUALLY_COMPLETED.value,
            RebalanceTransactionStates.SKIPPED.value,
        ],
        RebalanceTransactionStates.COMPLETED.value: [],
        RebalanceTransactionStates.MANUALLY_COMPLETED.value: [],
        RebalanceTransactionStates.SKIPPED.value: [],
    },
    CallbackStageType.ORDER.value: {
        OrderCurrentStatus.WAITING.value: [
            OrderCurrentStatus.BUY_IN_PROGRESS.value,
            OrderCurrentStatus.SKIP.value,
        ],
        OrderCurrentStatus.BUY_IN_PROGRESS.value: [
            OrderCurrentStatus.BUY.value,
            OrderCurrentStatus.SKIP.value,
        ],
        OrderCurrentStatus.BUY.value: [
            OrderCurrentStatus.SL_WAITING.value,
            OrderCurrentStatus.SELL_IN_PROGRESS.value,
            OrderCurrentStatus.SKIP.value,
        ],
        OrderCurrentStatus.SL_WAITING.value: [
            OrderCurrentStatus.SL_PLACED.value,
            OrderCurrentStatus.SELL_IN_PROGRESS.value,
            OrderCurrentStatus.SKIP.value,
        ],
        OrderCurrentStatus.SL_PLACED.value: [
            OrderCurrentStatus.SELL_IN_PROGRESS.value,
            OrderCurrentStatus.SKIP.value,
        ],
        OrderCurrentStatus.SELL_IN_PROGRESS.value: [
            OrderCurrentStatus.SELL.value,
            OrderCurrentStatus.SKIP.value,
        ],
        OrderCurrentStatus.SELL.value: [],
        OrderCurrentStatus.SKIP.value: [],
    },
    CallbackStageType.BASKET.value: {
        BasketStates.UNINVESTED.value: [BasketStates.WAITING.value],
        BasketStates.WAITING.value: [
            BasketStates.MONITORING.value,
            BasketStates.COMPLETE.value,
        ],
        BasketStates.MONITORING.value: [BasketStates.COMPLETE.value],
        BasketStates.COMPLETE.value: [],
    },
}


def is_terminal(stage_type: str, state: str) -> bool:
    """Return whether ``state`` has no legal outgoing transitions.

    Returns ``False`` for states not present in ``ALLOWED`` so unknown
    legacy values do not silently appear "done". Callers that need to
    distinguish "unknown state" from "terminal state" must validate
    membership against ``ALLOWED[stage_type]`` separately.
    """
    transitions = ALLOWED.get(stage_type, {})
    return state in transitions and not transitions[state]


def is_allowed(
    stage_type: str,
    from_state: str | None,
    to_state: str,
) -> bool:
    """Return whether the matrix permits ``from_state`` to ``to_state``."""
    if from_state is None:
        return INITIAL_STATES.get(stage_type) == to_state
    return to_state in ALLOWED.get(stage_type, {}).get(from_state, [])
