"""
    Module for Admin Models.
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.holdings.models import Transaction, Holding, Position
from multitenant.admin_site import tenant_admin_site
from multitenant.tenantawareadmin import TenantAwareModelAdmin


# Register your models here.

class TransactionAdminModel(TenantAwareModelAdmin):
    """
    Admin model for Transaction
    """
    list_display = ('id', 'created', 'modified', 'user_portfolio', 'source', 'target', 'amount', 'type', 'current_state')
    list_filter = ('type', 'current_state')
    search_fields = ('type', 'current_state')


class HoldingAdminModel(TenantAwareModelAdmin):
    """
    Admin model for Holding
    """

    def value(self, obj):
        return obj.quantity * obj.avg_buy_price

    def holding_thresholds(self, obj):
        """Link to Holding Thresholds for this holding."""
        url_name = 'tenant_admin:alerts_holdingthreshold_changelist'
        link_url = reverse(url_name)
        link_url += f"?holding_type=Security&holding_id={obj.id}"
        return format_html("<a href='{url}' target='_blank'>{text}</a>",
                           url=link_url,
                           text='Holding Thresholds')

    list_display = ('id', 'created', 'modified', 'user_portfolio', 'symbol', 'quantity', 'avg_buy_price', 'value',
                    'holding_thresholds')
    list_filter = ('symbol',)
    search_fields = ('symbol',)


class PositionAdmin(TenantAwareModelAdmin):
    """
    Admin view for the Position model.
    Provides detailed views and management of user portfolio holdings,
    including filtering and search options.
    """

    list_display = (
        'id',
        'basket',
        'symbol',
        'buy_price',
        'quantity',
        'created',
        'modified'
    )
    list_filter = ('basket', 'symbol', 'created', 'modified')
    search_fields = ('symbol', 'basket__user_id')

    fieldsets = (
        (None, {
            'fields': ('basket', 'symbol')
        }),
        ('Holding Details', {
            'fields': ('buy_price', 'quantity')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified')
        }),
    )
    readonly_fields = ('created', 'modified')

    ordering = ('-created',)


tenant_admin_site.register(Transaction, TransactionAdminModel)
tenant_admin_site.register(Holding, HoldingAdminModel)
tenant_admin_site.register(Position, PositionAdmin)
