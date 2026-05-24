"""
Structured logging for lifecycle state writes — Phase 0 / D2.

This module exposes :class:`StateLogger`, the single entry point that
Phase 1's ``TransitionService`` (and any other code mutating lifecycle
state) calls to record what happened. Every emission is:

* tagged with a request-scoped ``correlation_id`` pulled from
  ``log_request_id`` (wired in ``configurations/base.py``),
* written on one line in ``key=value`` form so it is greppable from a
  terminal and easy for structured-log shippers to parse,
* free of side effects beyond the ``logging`` call — no DB writes, no
  metric backends. Wire those in alongside the metrics infrastructure
  outlined in plan §10.

A module-level singleton named ``state_logger`` is provided for the
common case::

    from apps.portfolio.services.state_logging import state_logger

    state_logger.log_state_change(
        stage_type="phase",
        stage_id=phase.id,
        from_state="processing",
        to_state="completed",
        actor="trade-placement",
        trigger="callback",
    )

Tests or alternate wirings can instantiate :class:`StateLogger` with a
custom ``logger_name`` to route output elsewhere.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

try:
    # ``log_request_id`` stores the active request id on a thread-local
    # / context-local. Reading it here lets the helper also work from
    # places the formatter's ``request_id`` filter does not cover, such
    # as Celery tasks before the worker sets one.
    from log_request_id import local as _request_local
except ImportError:  # pragma: no cover - non-Django invocation
    _request_local = None


DEFAULT_LOGGER_NAME = "apps.portfolio.state"
_MISSING_VALUE = "-"


class StateLogger:
    """Emit single-line, structured log records for lifecycle events.

    The class is deliberately small and stateless apart from its
    underlying :class:`logging.Logger`. A module-level singleton
    (``state_logger``) is provided for code that does not need to
    customise the logger name.

    Output format::

        event=<name> correlation_id=<id> key=value key=value ...

    ``None`` values are rendered as ``-`` so columns line up when the
    log is scanned by eye. Canonical fields are emitted in a stable
    order; any ``extra`` keys follow in sorted order so grep / awk
    pipelines remain stable.
    """

    def __init__(self, logger_name: str = DEFAULT_LOGGER_NAME) -> None:
        """Bind this instance to a named :class:`logging.Logger`.

        :param logger_name: Dotted logger name. Defaults to
            ``apps.portfolio.state`` which already has handlers wired
            in ``configurations/base.py``.
        """
        self._logger = logging.getLogger(logger_name)
        self._logger.debug(f"StateLogger initialised logger={logger_name}")

    def log_state_change(
        self,
        *,
        stage_type: str,
        stage_id: Any,
        from_state: Optional[str],
        to_state: str,
        actor: str,
        trigger: str,
        product_type: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        guard_code: Optional[str] = None,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Record a single lifecycle state transition.

        Call from inside ``TransitionService.transition`` after the
        row has been locked and the new state has been committed so
        successes, no-ops, and failures all land in the same stream.

        :param stage_type: Polymorphic stage discriminator —
            ``portfolio`` / ``rebalance_event`` / ``phase`` /
            ``order`` / ``basket``.
        :param stage_id: Primary key of the stage row.
        :param from_state: State before the transition. ``None`` for
            newly created rows.
        :param to_state: State after the transition.
        :param actor: User id, service name, or ``system``.
        :param trigger: What caused the transition — ``api`` /
            ``callback`` / ``scheduled`` / ``manual`` / ``system``.
        :param product_type: Owning portfolio's product type, useful
            for slicing dashboards by product.
        :param idempotency_key: Callback idempotency key when the
            trigger is a callback.
        :param guard_code: Identifier of the guard that approved (or
            on failure rejected) the transition.
        :param extra: Arbitrary additional context. Keys are emitted
            in sorted order after the canonical fields.
        """
        fields = {
            "stage_type": stage_type,
            "stage_id": stage_id,
            "from_state": from_state,
            "to_state": to_state,
            "actor": actor,
            "trigger": trigger,
            "product_type": product_type,
            "idempotency_key": idempotency_key,
            "guard_code": guard_code,
        }
        self._emit("state_change", fields, extra)

    def log_callback(
        self,
        *,
        stage_type: str,
        stage_id: Any,
        direction: str,
        target_service: str,
        callback_ref: str,
        idempotency_key: str,
        status: str,
        duplicate: bool = False,
        reason: Optional[str] = None,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Record a callback flowing through the lifecycle layer.

        ``duplicate=True`` indicates the call was deduped by
        ``idempotency_key`` and did not advance state. Phase 1 sets
        this when ``CallbackLog`` already has a ``completed`` row
        for the same key.

        :param stage_type: Stage type the callback pertains to.
        :param stage_id: Stage id the callback pertains to.
        :param direction: ``inbound`` or ``outbound``.
        :param target_service: Counterparty service name.
        :param callback_ref: External counterparty's correlation id.
        :param idempotency_key: Composite idempotency key per
            plan §7.7.
        :param status: ``processing`` / ``completed`` / ``failed``.
        :param duplicate: ``True`` if this delivery was deduped and
            therefore a no-op.
        :param reason: Failure detail when ``status`` is ``failed``.
        :param extra: Arbitrary additional context.
        """
        fields = {
            "stage_type": stage_type,
            "stage_id": stage_id,
            "direction": direction,
            "target_service": target_service,
            "callback_ref": callback_ref,
            "idempotency_key": idempotency_key,
            "status": status,
            "duplicate": duplicate,
            "reason": reason,
        }
        self._emit("callback", fields, extra)

    def _emit(
        self,
        event: str,
        fields: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]],
    ) -> None:
        """Serialise ``fields`` and ``extra`` into a single log line.

        Builds a ``key=value``-token string and pushes it through the
        bound logger at INFO level. ``correlation_id`` is sourced from
        :meth:`_current_correlation_id` and always appears immediately
        after the ``event`` token.
        """
        correlation_id = self._current_correlation_id()
        body_parts = [f"{k}={self._render(v)}" for k, v in fields.items()]
        if extra:
            body_parts.extend(
                f"{k}={self._render(v)}" for k, v in sorted(extra.items())
            )
        body = " ".join(body_parts)
        cid = self._render(correlation_id)
        self._logger.info(f"event={event} correlation_id={cid} {body}")

    @staticmethod
    def _render(value: Any) -> str:
        """Stringify ``value`` for inclusion in a ``key=value`` token.

        ``None`` becomes ``-``. Strings containing whitespace are
        wrapped in double quotes (with any embedded quotes escaped)
        so the line stays parseable when split on whitespace.
        """
        if value is None:
            return _MISSING_VALUE
        text = str(value)
        if any(ch.isspace() for ch in text):
            escaped = text.replace('"', '\\"')
            return f'"{escaped}"'
        return text

    @staticmethod
    def _current_correlation_id() -> Optional[str]:
        """Return the active request correlation id, if any.

        Returns ``None`` when ``log_request_id`` is unavailable (e.g.
        the module was imported outside a Django process) or when no
        request id has been bound to the current thread / context.
        """
        if _request_local is None:
            return None
        return getattr(_request_local, "request_id", None)


# Module-level singleton — import this for the common case.
state_logger = StateLogger()
