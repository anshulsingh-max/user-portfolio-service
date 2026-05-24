"""Lifecycle constants and enum choices."""

from __future__ import annotations

from enum import Enum


class CallbackLogStatus(Enum):
    (
        "Status of a CallbackLog entry — same values as "
        "PhaseCallbackLogEnum."
    )
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

    CHOICES = (
        (PROCESSING, PROCESSING),
        (COMPLETED, COMPLETED),
        (FAILED, FAILED),
    )


class CallbackDirection(Enum):
    """Whether a callback came in to us or we sent it out."""
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'

    CHOICES = (
        (INBOUND, INBOUND),
        (OUTBOUND, OUTBOUND),
    )


class CallbackStageType(Enum):
    """Which legacy lifecycle entity a CallbackLog row refers to.

    Polymorphic reference used by the Phase 1 TransitionService (§7.4).
    """
    PORTFOLIO = 'portfolio'
    REBALANCE_EVENT = 'rebalance_event'
    PHASE = 'phase'
    ORDER = 'order'
    BASKET = 'basket'

    CHOICES = (
        (PORTFOLIO, PORTFOLIO),
        (REBALANCE_EVENT, REBALANCE_EVENT),
        (PHASE, PHASE),
        (ORDER, ORDER),
        (BASKET, BASKET),
    )


class LifecycleEventType(Enum):
    """Types of append-only rows emitted by the lifecycle authority."""
    CREATED = 'created'
    STATE_CHANGED = 'state_changed'
    TRANSITION_APPLIED = 'transition_applied'
    GUARD_FAILED = 'guard_failed'
    LEG_UPDATED = 'leg_updated'
    ERROR = 'error'

    CHOICES = (
        (CREATED, CREATED),
        (STATE_CHANGED, STATE_CHANGED),
        (TRANSITION_APPLIED, TRANSITION_APPLIED),
        (GUARD_FAILED, GUARD_FAILED),
        (LEG_UPDATED, LEG_UPDATED),
        (ERROR, ERROR),
    )


class LifecycleEventTrigger(Enum):
    """Sources that can legitimately request a lifecycle transition."""
    API = 'api'
    CALLBACK = 'callback'
    SCHEDULED = 'scheduled'
    MANUAL = 'manual'
    SYSTEM = 'system'

    CHOICES = (
        (API, API),
        (CALLBACK, CALLBACK),
        (SCHEDULED, SCHEDULED),
        (MANUAL, MANUAL),
        (SYSTEM, SYSTEM),
    )
