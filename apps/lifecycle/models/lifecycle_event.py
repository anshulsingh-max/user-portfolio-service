"""Lifecycle event history for Phase 1 state authority.

The model records human-readable transition history without coupling the
legacy lifecycle tables to a shared concrete parent table.
"""

from __future__ import annotations

from django.db import models

from apps.lifecycle.constants import (
    CallbackStageType,
    LifecycleEventTrigger,
    LifecycleEventType,
)


class LifecycleEvent(models.Model):
    """Append-only lifecycle log described in plan section 7.2.

    Rows are append-only by PR discipline and must never be updated or
    deleted, though this pass does not enforce that at the database layer.
    The target stage is polymorphic: ``stage_type`` and ``stage_id`` point
    at one of several legacy tables, so this is intentionally not a foreign
    key. ``CallbackLog`` remains the authoritative unique deduplication
    record; ``LifecycleEvent`` is the readable transition log, and a single
    callback may legitimately emit several rows.
    """

    class Meta:
        db_table = 'lifecycle_event'
        indexes = [
            models.Index(
                fields=['stage_type', 'stage_id', 'occurred_at'],
                name='lcevt_stage_occ_idx',
            ),
        ]
        ordering = ['occurred_at', 'id']

    stage_type = models.CharField(
        max_length=32,
        choices=CallbackStageType.CHOICES.value,
    )
    stage_id = models.BigIntegerField()
    event_type = models.CharField(
        max_length=32,
        choices=LifecycleEventType.CHOICES.value,
    )
    from_state = models.CharField(max_length=50, null=True, blank=True)
    to_state = models.CharField(max_length=50, null=True, blank=True)
    actor = models.CharField(max_length=128)
    trigger = models.CharField(
        max_length=32,
        choices=LifecycleEventTrigger.CHOICES.value,
    )
    guard_code = models.CharField(max_length=64, null=True, blank=True)
    idempotency_key = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    correlation_id = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        db_index=True,
    )
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(auto_now_add=True)
