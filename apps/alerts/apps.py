from django.apps import AppConfig


class AlertsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.alerts"

    def ready(self):
        from apps.alerts import signals
        import apps.portfolio.admin
        from user_portfolio.tenants import register_tenant_dbs
        register_tenant_dbs()
