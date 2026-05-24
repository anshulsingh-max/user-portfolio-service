"""
    Module for Admin Models.
"""
from django.urls import reverse
from django.utils.html import format_html

from apps.portfolio.models import UserPortfolio, UserPortfolioRebalance, UserInstruction, Order, OrderInstruction, \
    Basket, PortfolioRebalanceTransaction
from multitenant.tenant_context import inject_tenant
from multitenant.tenantawareadmin import TenantAwareModelAdmin
from multitenant.admin_site import tenant_admin_site


# Register your models here.

class UserPortfolioAdminModel(TenantAwareModelAdmin):
    """
        Admin model for User Portfolio Data
    """
    list_display = ('id', 'created', 'modified', 'investment_date',
                    'user_id', 'name', 'portfolio_id', 'product_type', 'strategy', 'broker', 'status', 'deactivated_reason', 'proxy', 'proxy_id',
                    "expected_investment", 'invested_amount', 'mtf_invested_amount', 'remaining_amount',
                    "average_leverage",
                    'subscription_id', 'user_portfolio_rebalances', 'holdings', 'transactions')
    list_filter = ('user_id', 'name', 'portfolio_id', 'broker', 'proxy', 'product_type', 'strategy')
    search_fields = ('user_id', 'portfolio_id', 'broker')

    def user_portfolio_rebalances(self, obj):
        """
        Generates an HTML link to the User Portfolio Rebalance page for a given object.

        This method constructs a URL for the User Portfolio Rebalance page using the object's ID,
        and formats it as an HTML link that opens in a new tab.

        Args:
            obj (Any): The object from which the ID is extracted.

        Returns:
            str: An HTML link to the User Portfolio Rebalance page.
        """
        link_url = reverse(f'tenant_admin:{obj._meta.app_label}_{"userportfoliorebalance"}_changelist')
        link_url += f"?user_portfolio={str(obj.id)}"
        link_url = inject_tenant(link_url, self.tenant_id)
        return format_html("<a href='{url}' target='_blank'>{text}</a>",
                           url=link_url,
                           text='User Portfolio Rebalance')

    def holdings(self, obj):
        """
        Generates an HTML link to the User Holding page for a given object.

        This method constructs a URL for the User Holding page using the object's ID,
        and formats it as an HTML link that opens in a new tab.

        Args:
            obj (Any): The object from which the ID is extracted.

        Returns:
            str: An HTML link to the User Holding page.
        """

        url_name = 'tenant_admin:holdings_holding_changelist'
        link_url = reverse(url_name)
        link_url += f"?user_portfolio={str(obj.id)}"
        return format_html('<a href="{url}">{text}</a>',
                           url=link_url,
                           text='User Holding')

    def transactions(self, obj):
        """
        Generates an HTML link to the Transactions page for a given object.

        This method constructs a URL for the Transactions page using the object's ID,
        and formats it as an HTML link that opens in a new tab.

        Args:
            obj (Any): The object from which the ID is extracted.

        Returns:
            str: An HTML link to the Transactions page.
        """
        url_name = 'tenant_admin:holdings_transaction_changelist'
        link_url = reverse(url_name)
        link_url += f"?user_portfolio={str(obj.id)}"
        return format_html("<a href='{url}' target='_blank'>{text}</a>",
                           url=link_url,
                           text='Transactions')


class UserPortfolioRebalanceAdminModel(TenantAwareModelAdmin):
    """
    Admin model for User Portfolio Rebalance
    """
    list_display = ('id', 'created', 'modified', 'user_portfolio', 'type', 'states', 'current_state',
                    'rebalance_id', 'user_inputs', 'cash_ingested', 'cash_carry_forward',
                    'transaction_type', 'transaction', 'proxy', 'instructions_url', 'portfolio_rebalances',
                    'proxy_id', 'rebalance_strategy', 'reason')
    list_filter = ('current_state', 'transaction_type', 'proxy', 'rebalance_strategy')
    search_fields = ('current_state', 'transaction_type')

    def portfolio_rebalances(self, obj):
        """
        Generates an HTML link to the Portfolio Rebalance page for a given object.

        This method constructs a URL for the Portfolio Rebalance page using the object's ID,
        and formats it as an HTML link that opens in a new tab.

        Args:
            obj (Any): The object from which the ID is extracted.

        Returns:
            str: An HTML link to the Portfolio Rebalance page.
        """
        link_url = reverse(f'tenant_admin:{obj._meta.app_label}_{"portfoliorebalancetransaction"}_changelist')
        link_url += f"?portfolio_rebalance={str(obj.id)}"
        link_url = inject_tenant(link_url, self.tenant_id)
        return format_html("<a href='{url}' target='_blank'>{text}</a>",
                           url=link_url,
                           text='Portfolio Rebalance')

    def instructions_url(self, obj):
        """
        Generates a clickable HTML link for the instruction_url field.

        This method formats the 'instruction_url' field as a clickable link
        with the text 'Instructions'. When clicked, the link opens the URL
        in a new browser tab.

        Args:
            obj (UserPortfolioRebalance): The instance of the UserPortfolioRebalance model.

        Returns:
            str: HTML string rendering the instruction_url as a clickable link.
        """
        if obj.instruction_url:
            return format_html("<a href='{url}' target='_blank'>{text}</a>",
                               url=obj.instruction_url,
                               text='Instructions')


class UserInstructionAdminModel(TenantAwareModelAdmin):
    """
        Admin model for User Instruction
    """
    list_display = ('id', 'created', 'modified', 'portfolio_rebalance_transaction', 'trade_placement_id', 'order_tag',
                    'symbol', 'quantity', 'filled_quantity', 'leverage', 'side', 'value', 'status', "reason", 'asm_consent',
                    'asm_reason', 'price')
    list_filter = ('symbol', 'side', 'status', 'asm_consent')
    search_fields = ('symbol',)


class PortfolioRebalanceTransactionAdminModel(TenantAwareModelAdmin):
    """
    Admin model for Portfolio Rebalance Transaction
    """
    list_display = ('id', 'created', 'modified', 'portfolio_rebalance', 'allocation_quantity', 'user_rebalance_json',
                    'type', 'current_state', 'executed_list', 'amount', 'instructions_url', 'user_instructions')
    list_filter = ('current_state', 'current_state', 'type')
    search_fields = ('current_state', 'current_state', 'type')

    def user_instructions(self, obj):
        """
        Generates an HTML link to the User Instructions page for a given object.

        This method constructs a URL for the User Instructions page using the object's ID,
        and formats it as an HTML link that opens in a new tab.

        Args:
            obj (Any): The object from which the ID is extracted.

        Returns:
            str: An HTML link to the User Instructions page.
        """
        link_url = reverse(f'tenant_admin:{obj._meta.app_label}_{"userinstruction"}_changelist')
        link_url += f"?portfolio_rebalance_transaction={str(obj.id)}"
        link_url = inject_tenant(link_url, self.tenant_id)
        return format_html("<a href='{url}' target='_blank'>{text}</a>",
                           url=link_url,
                           text='User Instructions')

    def instructions_url(self, obj):
        """
        Generates a clickable HTML link for the instruction_url field.

        This method formats the 'instruction_url' field as a clickable link
        with the text 'Instructions'. When clicked, the link opens the URL
        in a new browser tab.

        Args:
            obj (UserPortfolioRebalance): The instance of the UserPortfolioRebalance model.

        Returns:
            str: HTML string rendering the instruction_url as a clickable link.
        """
        if obj.instruction_url:
            return format_html("<a href='{url}' target='_blank'>{text}</a>",
                               url=obj.instruction_url,
                               text='Instructions')


class BasketAdmin(TenantAwareModelAdmin):
    """
    Admin view for the Basket model.
    Provides options to display, filter, and search the Basket records.
    """

    list_display = (
        'id',
        'user_id',
        'current_state',
        'broker',
        'model_id',
        'basket_type',
        'product_type',
        'payment_id',
        'recommendation_id',
        'cash_ingested',
        'amount',
        'exposure_amount',
        'end_amount',
        'profit_target_1',
        'profit_target_1_value',
        'profit_target_2',
        'profit_target_2_value',
        'pt1_hit',
        'pt2_hit',
        'pt1_hit_time',
        'pt2_hit_time',
        'last_notification_sent',
        'created',
        'modified',
        'order',
        'positions',
        'profit',
    )
    list_filter = (
        'broker',
        'basket_type',
        'product_type',
        'current_state',
        'model_id',
        'recommendation_id',
        'pt1_hit',
        'pt2_hit',
        'created',
        'modified',
    )
    search_fields = ('user_id', 'payment_id', 'model_id', 'recommendation_id', 'broker')

    fieldsets = (
        (None, {
            'fields': ('user_id', 'current_state', 'model_id', 'payment_id', 'recommendation_id', 'broker')
        }),
        ('Allocation & Investments', {
            'fields': ('basket_type', 'product_type', 'user_allocation', 'cash_ingested', 'amount',
                       'exposure_amount', 'end_amount',
                       'profit_target_1', 'profit_target_1_value', 'profit_target_2', 'profit_target_2_value')
        }),
        ('Profit Target Hits', {
            'fields': ('pt1_hit', 'pt1_hit_time', 'pt2_hit', 'pt2_hit_time', 'last_notification_sent')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified')
        }),
    )
    readonly_fields = ('created', 'modified', 'exposure_amount')

    ordering = ('-created',)

    def order(self, obj):
        link_url = reverse(f'tenant_admin:{obj._meta.app_label}_{"order"}_changelist')
        link_url += f"?basket={str(obj.id)}"
        link_url = inject_tenant(link_url, self.tenant_id)
        return format_html("<a href='{url}' target='_blank'>{text}</a>",
                           url=link_url,
                           text='Order')

    def positions(self, obj):
        url_name = 'tenant_admin:holdings_position_changelist'
        link_url = reverse(url_name)
        link_url += f"?basket={str(obj.id)}"
        return format_html('<a href="{url}">{text}</a>',
                           url=link_url,
                           text='Positions')

    def profit(self, obj):
        end_amount = float(obj.end_amount) if obj.end_amount is not None else 0.0
        initial_amount = float(obj.amount) if obj.amount is not None else 0.0
        if end_amount and initial_amount:
            return end_amount - initial_amount


class OrderAdmin(TenantAwareModelAdmin):
    """
    Admin view for the Order model.
    Provides a detailed view of all fields, filtering, and search functionality.
    """

    list_display = (
        'id',
        'basket',
        'trading_symbol',
        'buy_price',
        'sell_price',
        'states',
        'current_status',
        'initial_amount',
        'end_amount',
        'stop_loss',
        'stop_loss_hit',
        'stop_loss_hit_time',
        'leverage',
        'created',
        'modified',
        'last_notification_sent',
        'order_instruction',
    )
    list_filter = (
        'states',
        'current_status',
        'basket__user_id',
        'stop_loss_hit',
        'created',
        'modified',
    )
    search_fields = ('trading_symbol', 'basket__user_id')

    fieldsets = (
        (None, {
            'fields': ('basket', 'trading_symbol', 'states', 'current_status')
        }),
        ('Order Details', {
            'fields': (
                'buy_price', 'sell_price', 'initial_amount', 'end_amount', 'stop_loss', 'leverage',
                'stop_loss_hit', 'stop_loss_hit_time', 'last_notification_sent'
            )
        }),
        ('Timestamps', {
            'fields': ('created', 'modified')
        }),
    )
    readonly_fields = ('created', 'modified')

    ordering = ('-created',)

    def order_instruction(self, obj):
        link_url = reverse(f'tenant_admin:{obj._meta.app_label}_{"orderinstruction"}_changelist')
        link_url += f"?order={str(obj.id)}"
        link_url = inject_tenant(link_url, self.tenant_id)
        return format_html("<a href='{url}' target='_blank'>{text}</a>",
                           url=link_url,
                           text='Order Instruction')


class OrderInstructionAdmin(TenantAwareModelAdmin):
    """
    Admin view for the OrderInstruction model.
    Provides detailed views and management of order instructions, including filtering and search options.
    """

    list_display = (
        'id',
        'order',
        'trade_placement_id',
        'order_tag',
        'symbol',
        'quantity',
        'filled_quantity',
        'order_price',
        'side',
        'value',
        'status',
        'source',
        'reason',
        'created',
        'modified'
    )
    list_filter = ('status', 'side', 'source', 'order__basket', 'created', 'modified')
    search_fields = ('order_tag', 'symbol', 'order__basket__user_id', 'trade_placement_id')

    fieldsets = (
        (None, {
            'fields': ('order', 'trade_placement_id', 'order_tag', 'symbol')
        }),
        ('Order Details', {
            'fields': ('quantity', 'filled_quantity', 'order_price', 'side', 'value', 'status')
        }),
        ('Additional Information', {
            'fields': ('reason',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified')
        }),
    )
    readonly_fields = ('created', 'modified')

    ordering = ('-created',)


tenant_admin_site.register(UserPortfolio, UserPortfolioAdminModel)
tenant_admin_site.register(UserPortfolioRebalance, UserPortfolioRebalanceAdminModel)
tenant_admin_site.register(UserInstruction, UserInstructionAdminModel)
tenant_admin_site.register(PortfolioRebalanceTransaction, PortfolioRebalanceTransactionAdminModel)
tenant_admin_site.register(Basket, BasketAdmin)
tenant_admin_site.register(Order, OrderAdmin)
tenant_admin_site.register(OrderInstruction, OrderInstructionAdmin)
