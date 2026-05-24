"""Lifecycle model mixins."""

from __future__ import annotations


class TimestampStrMixin:
    """Local copy of portfolio's TimestampStrMixin.

    Keeping the mixin local keeps the lifecycle app self-contained.
    Requires the host model to inherit from `TimeStampedModel`
    (django_extensions) so `created` and `modified` are present.
    """

    @property
    def created_str(self) -> str:
        """Return ``created`` as an ISO-8601 string."""
        return self.created.isoformat() if self.created else ""

    @property
    def modified_str(self) -> str:
        """Return ``modified`` as an ISO-8601 string."""
        return self.modified.isoformat() if self.modified else ""
