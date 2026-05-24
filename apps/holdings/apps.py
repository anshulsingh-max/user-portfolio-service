from django.apps import AppConfig


class HoldingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.holdings'

    def ready(self):
        from apps.holdings import signals
        from user_portfolio.tenants import register_tenant_dbs
        register_tenant_dbs()
