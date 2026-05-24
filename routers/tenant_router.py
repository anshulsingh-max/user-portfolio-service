import logging
from django.conf import settings

from multitenant.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class TenantDatabaseRouter:
    """
    A database router to control database operations based on the current tenant context.

    Routes read and write operations to the appropriate tenant database, and ensures
    that database relations and migrations follow the multi-tenant structure.
    """

    def __init__(self):
        self.default_tenant = 'default'

    def db_for_read(self, model, **hints):
        """
        Directs read operations to the appropriate tenant database.
        """
        if model._meta.app_label in ['auth', 'admin', 'contenttypes', 'sessions']:
            return 'default'
        tenant = get_current_tenant()
        if tenant in settings.DATABASES:
            logger.debug(f"[db_for_read] Routing read for model {model.__name__} to tenant DB: {tenant}")
            return tenant
        logger.debug(f"[db_for_read] Tenant '{tenant}' not found in TENANT_DATABASES. Using default DB.")
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Directs write operations to the appropriate tenant database.
        """
        if model._meta.app_label in ['auth', 'admin', 'contenttypes', 'sessions']:
            return 'default'
        tenant = get_current_tenant()
        if tenant in settings.DATABASES:
            logger.debug(f"[db_for_write] Routing write for model {model.__name__} to tenant DB: {tenant}")
            return tenant
        logger.debug(f"[db_for_write] Tenant '{tenant}' not found in TENANT_DATABASES. Using default DB.")
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Determines if a relation between two objects is allowed.
        Relations are only allowed if both objects are in the same database.
        """
        db_obj1 = self.db_for_read(obj1.__class__)
        db_obj2 = self.db_for_read(obj2.__class__)
        allowed = db_obj1 == db_obj2
        logger.debug(f"[allow_relation] Relation allowed: {allowed} (db1={db_obj1}, db2={db_obj2})")
        return allowed

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Allow migration on tenant-specific databases and default.
        """
        allowed = db in settings.DATABASES
        logger.debug(f"[allow_migrate] Migrate allowed on DB '{db}': {allowed}")
        return allowed
