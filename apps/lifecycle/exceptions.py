"""Exceptions raised by the lifecycle authority.

Typed exceptions carry enough context for callers and tests to distinguish
matrix violations from later guard failures.
"""

from __future__ import annotations

from typing import Any


class IllegalTransition(Exception):
    """Raised when a requested state change is absent from the matrix."""

    def __init__(
        self,
        *,
        stage_type: str,
        stage_id: Any,
        from_state: str | None,
        to_state: str,
    ) -> None:
        self.stage_type = stage_type
        self.stage_id = stage_id
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(str(self))

    def __str__(self) -> str:
        """Return operator-readable context for the blocked transition."""
        return (
            f"Illegal transition stage_type={self.stage_type} "
            f"id={self.stage_id} from={self.from_state} to={self.to_state}"
        )


class GuardFailed(Exception):
    """Raised when a future pre-transition guard rejects the change."""

    def __init__(
        self,
        *,
        guard_code: str,
        reason: str,
        stage_type: str,
        stage_id: Any,
    ) -> None:
        self.guard_code = guard_code
        self.reason = reason
        self.stage_type = stage_type
        self.stage_id = stage_id
        super().__init__(reason)
