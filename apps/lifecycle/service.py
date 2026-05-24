"""Row-locked lifecycle transition authority.

This module is the single writer for lifecycle state in the foundation layer:
it locks the stage row, checks idempotency, appends history, mutates through an
adapter, and defers side effects until the database commit succeeds.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from django.db import transaction

from apps.lifecycle.constants import (
    CallbackLogStatus,
    LifecycleEventType,
)
from apps.lifecycle.adapters import get_adapter
from apps.lifecycle.exceptions import IllegalTransition
from apps.lifecycle.models import CallbackLog, LifecycleEvent
from apps.lifecycle.transitions import is_allowed
from apps.lifecycle.state_logging import state_logger

try:
    from log_request_id import local as _request_local
except ImportError:  # pragma: no cover - non-Django invocation
    _request_local = None

logger = logging.getLogger(__name__)


def transition(
    stage: Any,
    to_state: str,
    *,
    actor: str,
    trigger: str,
    idempotency_key: str | None = None,
    guard_ctx: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any] | None = None,
) -> Any:
    """Single authority for lifecycle state writes.

    The row lock is acquired before idempotency lookup so concurrent callbacks
    for the same stage cannot both observe an incomplete dedup record.
    """
    adapter = get_adapter(stage)
    stage_type = adapter.stage_type

    with transaction.atomic():
        stage = adapter.lock_for_update(stage)

        if idempotency_key and CallbackLog.objects.filter(
            idempotency_key=idempotency_key,
            status=CallbackLogStatus.COMPLETED.value,
        ).exists():
            logger.info(
                f"transition skipped duplicate stage_type={stage_type} "
                f"id={stage.pk} key={idempotency_key}"
            )
            return stage

        from_state = adapter.get_state(stage)

        if not is_allowed(stage_type, from_state, to_state):
            logger.warning(
                f"transition illegal stage_type={stage_type} "
                f"id={stage.pk} from={from_state} to={to_state}"
            )
            raise IllegalTransition(
                stage_type=stage_type,
                stage_id=stage.pk,
                from_state=from_state,
                to_state=to_state,
            )

        _run_guards(stage, to_state, guard_ctx)

        LifecycleEvent.objects.create(
            stage_type=stage_type,
            stage_id=stage.pk,
            event_type=LifecycleEventType.STATE_CHANGED.value,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            trigger=trigger,
            idempotency_key=idempotency_key,
            correlation_id=_current_correlation_id(),
            payload=dict(payload or {}),
        )

        adapter.set_state(stage, to_state)

        state_logger.log_state_change(
            stage_type=stage_type,
            stage_id=stage.pk,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            trigger=trigger,
            idempotency_key=idempotency_key,
        )

        transaction.on_commit(
            lambda: _schedule_side_effects(stage_type, stage.pk, to_state)
        )

        logger.info(
            f"transition committed stage_type={stage_type} "
            f"id={stage.pk} from={from_state} to={to_state}"
        )
        return stage


def _run_guards(
    stage: Any,
    to_state: str,
    guard_ctx: Mapping[str, Any] | None,
) -> None:
    """Pre-transition guards; Phase 1 foundation accepts every request."""
    return None


def _schedule_side_effects(
    stage_type: str,
    stage_id: Any,
    to_state: str,
) -> None:
    """Side-effect dispatch placeholder for the later signal re-home pass."""
    logger.debug(
        f"side_effects stub stage_type={stage_type} "
        f"id={stage_id} to={to_state}"
    )


def _current_correlation_id() -> str | None:
    """Return the active request correlation id."""
    if _request_local is None:
        return None
    return getattr(_request_local, "request_id", None)


class TransitionService:
    """Thin facade around module-level transition() for DI in tests."""

    def transition(self, stage: Any, to_state: str, **kwargs: Any) -> Any:
        """Delegate to the module-level transition authority."""
        return transition(stage, to_state, **kwargs)
