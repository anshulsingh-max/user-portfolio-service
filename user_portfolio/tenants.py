import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def register_tenant_dbs():
    """
    Registers all tenant databases into Django's settings.DATABASES dynamically.
    This allows multi-tenant support using separate databases for each tenant.
    """
    for tenant, db_settings in settings.TENANT_DATABASES.items():
        if tenant in settings.DATABASES:
            logger.info(f"[register_tenant_dbs] Tenant DB '{tenant}' already exists in DATABASES. Skipping.")
            continue

        settings.DATABASES[tenant] = db_settings
        logger.debug(f"[register_tenant_dbs] Registered tenant DB: {tenant}")
