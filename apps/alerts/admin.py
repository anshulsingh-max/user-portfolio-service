from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from django.utils.html import format_html

from apps.alerts.constants import Status
from apps.alerts.models import UserPortfolioThreshold, HoldingThreshold
from multitenant.admin_site import tenant_admin_site
from multitenant.tenantawareadmin import TenantAwareModelAdmin


class UserPortfolioThresholdAdmin(TenantAwareModelAdmin):
    """
    Admin configuration for UserPortfolioThreshold model.

    Features:
    - Rich list display with portfolio identifiers, threshold details, and status.
    - Filtering by type, status, and source to support operational workflows.
    - Search across portfolio type/ID for quick access.
    - Read-only audit trail to ensure history is preserved.
    - Logical grouping of fields for better readability.
    """

    list_display = (
        "id",
        "portfolio_type",
        "portfolio_id",
        "side",
        "threshold_type",
        "target_pct",
        "target_value",
        "colored_status",
        "source",
        "source_id",
        "effective_from",
        "effective_to",
        "triggered_at",
        "last_notification_sent_at",
        "reason",
        "created",
        "modified",
    )

    list_filter = (
        "portfolio_type",
        "side",
        "threshold_type",
        "status",
        "source",
        ("effective_from", DateFieldListFilter),
        ("effective_to", DateFieldListFilter),
        ("triggered_at", DateFieldListFilter),
        ("last_notification_sent_at", DateFieldListFilter),
    )

    search_fields = (
        "portfolio_type",
        "portfolio_id",
        "id",
    )

    ordering = ("-effective_from",)

    date_hierarchy = "effective_from"

    readonly_fields = (
        "effective_from",
        "effective_to",
        "triggered_at",
        "last_notification_sent_at",
        "created",
        "modified",
        "history",
    )

    fieldsets = (
        ("Portfolio Binding", {
            "fields": (
                "portfolio_type",
                "portfolio_id",
                "side",
            )
        }),
        ("Threshold Rule", {
            "fields": (
                "threshold_type",
                "status",
                "source",
                "source_id",
            )
        }),
        ("Threshold Values", {
            "fields": (
                "target_pct",
                "target_value",
            )
        }),
        ("Effective Dates", {
            "fields": (
                "effective_from",
                "effective_to",
            )
        }),
        ("Monitoring & Notifications", {
            "fields": (
                "triggered_at",
                "last_notification_sent_at",
                "reason"
            )
        }),
        ("System Audit", {
            "fields": (
                "created",
                "modified",
                "history",
            ),
        }),
    )

    # Display status in dark colors & bold
    def colored_status(self, obj):
        color = "#006400" if obj.status == Status.ACTIVE else "#8B0000"
        return format_html('<span style="color: {}; font-weight: 600;">{}</span>', color, obj.get_status_display())

    colored_status.short_description = "Status"
    colored_status.admin_order_field = "status"


class HoldingThresholdAdmin(TenantAwareModelAdmin):
    """
    Django admin configuration for the HoldingThreshold model.

    Features:
    - List display of key fields
    - Search and filter options
    - Readonly fields for timestamps and history
    - Field grouping for better UI
    """

    # Fields to display in the changelist
    list_display = (
        'id',
        'holding_type',
        'holding_id',
        'side',
        'threshold_type',
        'get_threshold_type_display',
        'target_pct',
        'target_value',
        'colored_status',
        'source',
        'effective_from',
        'effective_to',
        'triggered_at',
        'last_notification_sent_at',
        'reason',
        'created',
        'modified',
    )

    # Fields you can click to go to edit page
    list_display_links = ('holding_type', 'holding_id', 'threshold_type')

    # Filters on the right sidebar
    list_filter = (
        'holding_type',
        'side',
        'threshold_type',
        'status',
        'source',
        'effective_from',
        'effective_to',
    )

    # Fields to search via search box
    search_fields = ('holding_type', 'holding_id', 'created', 'modified')

    # Ordering of records in the changelist
    ordering = ('holding_type', 'holding_id', 'side', 'threshold_type', '-effective_from')

    # Fields that are read-only in the admin form
    readonly_fields = (
        'effective_from',
        'triggered_at',
        'last_notification_sent_at',
        'created',
        'modified',
        'history',
    )

    # Field grouping in the edit form
    fieldsets = (
        ('Threshold Details', {
            'fields': (
                'holding_type',
                'holding_id',
                'side',
                'threshold_type',
                'target_pct',
                'target_value',
            )
        }),
        ('Status & Source', {
            'fields': ('status', 'source',)
        }),
        ('Timing', {
            'fields': ('effective_from', 'effective_to', 'triggered_at', 'last_notification_sent_at', 'reason')
        }),
        ('Audit Info', {
            'fields': ('created', 'modified')
        }),
    )

    # Optional: show colored status in changelist
    def colored_status(self, obj):
        # Use darker tones for better contrast & accessibility
        color = '#006400' if obj.status == Status.ACTIVE else '#8B0000'  # darkgreen / darkred
        return format_html('<span style="color: {}; font-weight: 600;">{}</span>', color, obj.get_status_display())

    colored_status.short_description = 'Status'
    colored_status.admin_order_field = 'status'

    # Optional: automatically set created_by / updated_by
    def save_model(self, request, obj, form, change):
        if not obj.created:
            obj.created = request.user.username
        obj.modified = request.user.username
        super().save_model(request, obj, form, change)

tenant_admin_site.register(HoldingThreshold, HoldingThresholdAdmin)
tenant_admin_site.register(UserPortfolioThreshold, UserPortfolioThresholdAdmin)
