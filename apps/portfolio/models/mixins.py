"""
Shared model mixins for the portfolio app.
"""


class TimestampStrMixin:
    """ISO-8601 string accessors for `created` / `modified`.

    Requires the host model to inherit from `TimeStampedModel`
    (django_extensions) so `created` and `modified` are present.
    """

    @property
    def created_str(self) -> str:
        return self.created.isoformat() if self.created else ""

    @property
    def modified_str(self) -> str:
        return self.modified.isoformat() if self.modified else ""
