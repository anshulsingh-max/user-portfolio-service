from django.apps import AppConfig


class PortfolioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.portfolio'

    def ready(self):
        from apps.portfolio import signals
        import apps.portfolio.admin
        from user_portfolio.tenants import register_tenant_dbs
        register_tenant_dbs()
