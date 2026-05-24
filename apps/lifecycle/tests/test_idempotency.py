"""Tests for lifecycle idempotency key composition."""

from __future__ import annotations

from django.test import SimpleTestCase

from apps.lifecycle.idempotency import build_idempotency_key


class IdempotencyKeyTests(SimpleTestCase):
    """Verify that callback dedup keys are stable and discriminating."""

    def test_same_inputs_produce_same_key(self) -> None:
        """Assert deterministic output for identical inputs."""
        kwargs = {
            "broker": "paper",
            "order_tag": "tag-1",
            "trade_placement_id": 1,
            "broker_event_id": "evt-1",
            "payload": {"status": "filled"},
        }
        self.assertEqual(
            build_idempotency_key(**kwargs),
            build_idempotency_key(**kwargs),
        )

    def test_payload_key_order_is_canonical(self) -> None:
        """Assert reordered JSON keys do not change the payload hash."""
        first = build_idempotency_key(
            broker="paper",
            order_tag="tag-1",
            trade_placement_id=1,
            broker_event_id="evt-1",
            payload={"a": 1, "b": 2},
        )
        second = build_idempotency_key(
            broker="paper",
            order_tag="tag-1",
            trade_placement_id=1,
            broker_event_id="evt-1",
            payload={"b": 2, "a": 1},
        )
        self.assertEqual(first, second)

    def test_none_and_empty_components_match(self) -> None:
        """Assert absent string components are normalised to empty strings."""
        none_key = build_idempotency_key(
            broker=None,
            order_tag=None,
            trade_placement_id=None,
            broker_event_id=None,
            payload=None,
        )
        empty_key = build_idempotency_key(
            broker="",
            order_tag="",
            trade_placement_id=None,
            broker_event_id="",
            payload={},
        )
        self.assertEqual(none_key, empty_key)

    def test_different_payloads_produce_different_keys(self) -> None:
        """Assert payload content participates in the dedup key."""
        first = build_idempotency_key(
            broker="paper",
            order_tag="tag-1",
            trade_placement_id=1,
            broker_event_id="evt-1",
            payload={"status": "filled"},
        )
        second = build_idempotency_key(
            broker="paper",
            order_tag="tag-1",
            trade_placement_id=1,
            broker_event_id="evt-1",
            payload={"status": "rejected"},
        )
        self.assertNotEqual(first, second)
