"""Admin registrations for lifecycle models."""

from __future__ import annotations

from typing import Any

from django.urls import reverse
from django.utils.html import format_html

from apps.lifecycle.constants import CallbackStageType
from apps.lifecycle.models import CallbackLog
from multitenant.admin_site import tenant_admin_site
from multitenant.tenant_context import inject_tenant
from multitenant.tenantawareadmin import TenantAwareModelAdmin


class CallbackLogAdmin(TenantAwareModelAdmin):
    """
    Admin view for the CallbackLog model.

    `CallbackLog` is the authoritative idempotency record for broker and
    inter-service callbacks introduced in Phase 0 (B7) and consumed by
    Phase 1's `TransitionService`. It uses a polymorphic
    `(stage_type, stage_id)` pair to point at the legacy lifecycle row
    awaiting the callback - there is no Django ForeignKey because
    `stage_type` resolves to several different tables (UserPortfolio,
    UserPortfolioRebalance, PortfolioRebalanceTransaction, Order, Basket).

    The admin is intentionally read-leaning:

    * `idempotency_key`, `callback_ref`, and the payload JSON blobs are
      readonly - they are written by the system and mutating them by hand
      would silently break dedup or audit trails.
    * `status` and `reason` remain editable so on-call can manually mark a
      stuck callback as `failed` and record why.
    * The `stage_link` column resolves the polymorphic pointer to a
      clickable link into the relevant admin changelist so operators can
      jump from a callback row straight to the affected lifecycle entity.

    Filters and search are tuned for the common debugging questions:
    "which callbacks for this basket/rebalance failed today", "find the
    callback by idempotency key", "all outbound callbacks to
    trade-placement".
    """

    _STAGE_ADMIN_TARGETS = {
        CallbackStageType.PORTFOLIO.value: (
            'portfolio_userportfolio',
            'User Portfolio',
        ),
        CallbackStageType.REBALANCE_EVENT.value: (
            'portfolio_userportfoliorebalance',
            'Rebalance',
        ),
        CallbackStageType.PHASE.value: (
            'portfolio_portfoliorebalancetransaction',
            'Phase',
        ),
        CallbackStageType.ORDER.value: ('portfolio_order', 'Order'),
        CallbackStageType.BASKET.value: ('portfolio_basket', 'Basket'),
    }

    list_display = (
        'id',
        'created',
        'modified',
        'stage_type',
        'stage_id',
        'stage_link',
        'direction',
        'target_service',
        'status',
        'callback_ref',
        'idempotency_key',
        'reason',
    )
    list_filter = (
        'stage_type',
        'direction',
        'target_service',
        'status',
        'created',
        'modified',
    )
    search_fields = (
        'callback_ref',
        'idempotency_key',
        'stage_id',
        'target_service',
        'reason',
    )
    ordering = ('-created',)

    fieldsets = (
        ('Routing', {
            'description': (
                'Where this callback came from / is going to, and which '
                'lifecycle entity it pertains to.'
            ),
            'fields': ('stage_type', 'stage_id', 'direction',
                       'target_service'),
        }),
        ('Idempotency', {
            'description': (
                'Identifiers used to dedupe repeat deliveries. '
                '`idempotency_key` is the authoritative dedup key; '
                '`callback_ref` is the external counterparty\'s id.'
            ),
            'fields': ('callback_ref', 'idempotency_key', 'status'),
        }),
        ('Payloads', {
            'description': (
                'Raw inbound request body and outbound response body. '
                'Stored verbatim for audit; do not edit by hand.'
            ),
            'classes': ('collapse',),
            'fields': ('request_payload', 'response_payload'),
        }),
        ('Diagnostics', {
            'description': (
                'Free-text failure detail for on-call. Editable so a human '
                'can document why a stuck callback was manually marked '
                'failed.'
            ),
            'fields': ('reason',),
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
        }),
    )

    readonly_fields = (
        'callback_ref',
        'idempotency_key',
        'request_payload',
        'response_payload',
        'created',
        'modified',
    )

    def stage_link(self, obj: Any) -> str:
        """
        Render an admin link to the polymorphic target for this callback.

        Falls back to a plain "-" if the `stage_type` is unrecognised
        or if `stage_id` is missing.
        """
        target = self._STAGE_ADMIN_TARGETS.get(obj.stage_type)
        if not target or not obj.stage_id:
            return '-'
        url_basename, label = target
        try:
            link_url = reverse(
                f'tenant_admin:{url_basename}_change',
                args=[obj.stage_id],
            )
        except Exception:
            return f'{label} #{obj.stage_id}'
        link_url = inject_tenant(link_url, self.tenant_id)
        return format_html(
            "<a href='{url}' target='_blank'>{text}</a>",
            url=link_url,
            text=f'{label} #{obj.stage_id}',
        )

    stage_link.short_description = 'Stage'


tenant_admin_site.register(CallbackLog, CallbackLogAdmin)
