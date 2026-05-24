"""Public lifecycle authority API."""

from __future__ import annotations

from apps.lifecycle.exceptions import GuardFailed, IllegalTransition
from apps.lifecycle.idempotency import build_idempotency_key
from apps.lifecycle.service import TransitionService, transition

__all__ = [
    "IllegalTransition",
    "GuardFailed",
    "TransitionService",
    "transition",
    "build_idempotency_key",
]
