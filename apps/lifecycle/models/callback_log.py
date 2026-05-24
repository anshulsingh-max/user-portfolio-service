"""CallbackLog — Phase 0 / B7 (prep for Phase 1).

Schema per §7.3 of the unification plan. Records broker / async callbacks
with a unique idempotency key so duplicate callbacks are no-ops. Will be
the authoritative idempotency record once TransitionService (Phase 1) is
introduced; until then it is unused and read-only.

Polymorphic reference: (stage_type, stage_id) points at the legacy
lifecycle row awaiting the callback. No FK — different stage_types live
in different tables.
"""

from __future__ import annotations

from django.db import models
from django_extensions.db.models import TimeStampedModel

from apps.lifecycle.constants import (
    CallbackDirection,
    CallbackLogStatus,
    CallbackStageType,
)
from apps.lifecycle.models.mixins import TimestampStrMixin


class CallbackLog(TimestampStrMixin, TimeStampedModel):
    """
    Append-only audit + idempotency record for broker and inter-service
    callbacks crossing the lifecycle boundary.

    Why this exists
    ---------------
    Today the codebase has no single, reliable place that records "we
    received / sent this callback". The only existing artifact is
    :class:`PhaseCallbackLog`, which is specific to the
    rebalance → buy-after-sell phase handoff and does not cover the
    basket / MTF flow, broker fills, or outbound calls. That gap has
    bitten production at least once: a duplicate callback was
    processed twice because nothing said "we already handled this
    idempotency key". ``CallbackLog`` is the generalised replacement
    introduced in Phase 0 (item **B7** of the unification plan,
    schema per **§7.3**) so Phase 1's ``TransitionService`` has
    something to dedupe against from day one.

    Role in the system
    ------------------
    * **Phase 0 (now):** the table is created and exposed in the admin
      but no production code path writes to it yet. Treat it as a
      forward placeholder — wiring callers in Phase 0 risks coupling
      to a contract that may still shift.
    * **Phase 1:** ``TransitionService`` becomes the sole writer.
      Every inbound broker callback and every outbound call we make
      to ``trade-placement`` / ``rebalancing-business-service`` first
      consults ``CallbackLog`` by ``idempotency_key``; a row with
      ``status='completed'`` short-circuits the work as a no-op
      (plan §7.4). Successful processing flips the row to
      ``completed``; failures flip it to ``failed`` and record
      ``reason``.
    * **Phase 2+:** the table carries over unchanged; only the
      lifecycle tables it points at get merged.

    Polymorphic target — ``(stage_type, stage_id)``
    -----------------------------------------------
    Callbacks can target several different lifecycle rows that live in
    different tables (``UserPortfolio`` / ``UserPortfolioRebalance`` /
    ``PortfolioRebalanceTransaction`` / ``Order`` / ``Basket``). A
    real ``ForeignKey`` would force a single target table, so the
    reference is intentionally untyped at the schema level:
    ``stage_type`` discriminates which table ``stage_id`` belongs to.
    Resolving the pointer to a real object is the caller's
    responsibility — the admin's ``stage_link`` column is the
    reference implementation.

    Idempotency contract
    --------------------
    ``idempotency_key`` is the authoritative dedup key. Plan §7.7
    specifies the composition as
    ``broker + order_tag + trade_placement_id + broker_event_id +
    payload-hash``; this model only enforces uniqueness, not the
    composition. A duplicate delivery — same key — MUST be treated as
    a no-op, not an error.

    ``callback_ref`` is the *external* correlation id supplied by the
    counterparty (the legacy ``PhaseCallbackLog.phase_id`` plays this
    role for the old phase callback flow). It is unique so an
    operator can paste a value from broker logs and find the row, but
    dedup is keyed off ``idempotency_key`` so callers can dedupe even
    when the counterparty fails to send a ``callback_ref``.

    Lifecycle of a row
    ------------------
    1. Created with ``status='processing'`` the moment a callback
       enters the boundary.
    2. ``request_payload`` is set from the raw inbound body (or the
       outbound request body, depending on ``direction``).
    3. The transition runs. On success: ``status='completed'``,
       ``response_payload`` populated.
    4. On failure: ``status='failed'``, ``reason`` populated with the
       failure detail.
    5. Rows are never updated again after reaching a terminal
       status. The table is append-only in spirit; the admin keeps
       ``idempotency_key`` / ``callback_ref`` / payloads readonly
       so hand edits cannot silently break dedup or audit.

    Fields
    ------
    stage_type : CharField(choices=CallbackStageType)
        Which lifecycle entity this callback targets. One of
        ``portfolio`` / ``rebalance_event`` / ``phase`` / ``order``
        / ``basket``. Combined with :attr:`stage_id` to form the
        polymorphic pointer.
    stage_id : BigIntegerField
        Primary key of the row in the table chosen by
        :attr:`stage_type`. Not a ``ForeignKey`` because the target
        table varies.
    callback_ref : CharField(unique=True)
        External correlation id supplied by the counterparty. Used
        for human lookups; not a dedup key.
    direction : CharField(choices=CallbackDirection)
        ``inbound`` for callbacks delivered to us, ``outbound`` for
        calls we initiate. Lets dashboards split incoming broker
        traffic from outgoing requests.
    target_service : CharField
        Counterparty service name — e.g. ``trade-placement``,
        ``rebalancing-business-service``. Free-text rather than an
        enum because new services come and go.
    status : CharField(choices=CallbackLogStatus, default=processing)
        Lifecycle status of the callback itself, not the lifecycle
        row it targets. Defaults to ``processing`` at create time
        and ends at ``completed`` or ``failed``.
    idempotency_key : CharField(unique=True)
        Authoritative dedup key (see "Idempotency contract" above).
        Uniqueness is enforced at the DB level so concurrent
        duplicate deliveries cannot both win.
    request_payload : JSONField(default=dict)
        Raw payload that triggered the callback. Verbatim, for audit.
    response_payload : JSONField(default=dict)
        Raw payload returned to the counterparty (outbound) or
        produced while processing (inbound).
    reason : TextField(null=True, blank=True)
        Free-text failure detail. Populated when ``status='failed'``;
        also used by operators who manually mark a stuck row failed.
    created, modified : DateTimeField (from TimeStampedModel)
        Automatic timestamps. ``created`` doubles as the receipt
        time of the callback.

    Indexes & constraints
    ---------------------
    * ``callback_ref`` — UNIQUE
    * ``idempotency_key`` — UNIQUE (the dedup guard)
    * ``(stage_type, stage_id)`` — composite B-tree index named
      ``cblog_stage_idx`` so "all callbacks for this basket" / "all
      callbacks for this rebalance" queries stay cheap as the table
      grows.

    Compared with :class:`PhaseCallbackLog`
    ---------------------------------------
    ``PhaseCallbackLog`` is the legacy, narrow predecessor: tied to
    ``PortfolioRebalanceTransaction`` via a real FK, no
    ``idempotency_key``, no ``direction``, no ``target_service``,
    no payload columns. It stays in place during Phase 1 so existing
    rebalance flows keep working; new callers should write to
    ``CallbackLog`` instead.

    See also
    --------
    * :mod:`apps.lifecycle.state_logging` — emits the
      structured log line Phase 1 will pair with each row written
      here (``log_callback``).
    * Plan §7.3 (schema), §7.4 (TransitionService contract),
      §7.7 (idempotency key composition).
    """

    class Meta:
        db_table = 'callback_log'
        indexes = [
            models.Index(
                fields=['stage_type', 'stage_id'],
                name='cblog_stage_idx',
            ),
        ]

    stage_type = models.CharField(
        max_length=32,
        choices=CallbackStageType.CHOICES.value,
    )
    stage_id = models.BigIntegerField()
    callback_ref = models.CharField(max_length=128, unique=True)
    direction = models.CharField(
        max_length=16,
        choices=CallbackDirection.CHOICES.value,
    )
    target_service = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=CallbackLogStatus.CHOICES.value,
        default=CallbackLogStatus.PROCESSING.value,
    )
    idempotency_key = models.CharField(max_length=256, unique=True)
    request_payload = models.JSONField(default=dict)
    response_payload = models.JSONField(default=dict)
    reason = models.TextField(null=True, blank=True)
