"""Idempotency key composition for lifecycle callbacks.

The key remains operator-readable while canonicalising payloads so repeated
deliveries with reordered JSON collapse to the same deduplication value.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def hash_payload(payload: Mapping[str, Any] | None) -> str:
    """Return the canonical SHA-256 hash for a callback payload."""
    canonical = json.dumps(
        payload or {},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_idempotency_key(
    *,
    broker: str | None,
    order_tag: str | int | None,
    trade_placement_id: int | None,
    broker_event_id: str | None,
    payload: Mapping[str, Any] | None,
) -> str:
    """Build composite idempotency key per plan section 7.7.

    Composition: broker | order_tag | trade_placement_id | broker_event_id
    | sha256(canonical-json(payload)). Missing components render as the
    empty string so None and "" hash to the same key. The payload is
    canonicalised with sort_keys + compact separators so semantically
    equal payloads with different key order produce the same hash.
    """
    parts = [
        broker or "",
        "" if order_tag is None else str(order_tag),
        "" if trade_placement_id is None else str(trade_placement_id),
        broker_event_id or "",
        hash_payload(payload),
    ]
    return "|".join(parts)
