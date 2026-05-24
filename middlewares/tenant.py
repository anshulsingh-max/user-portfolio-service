import logging
import re

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from multitenant.tenant_context import set_current_tenant

logger = logging.getLogger('apps.tenant')


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to set tenant context either from the URL or headers.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.default_tenant = 'default'

    def process_request(self, request):
        path = request.path
        tenant_id = None
        match = re.match(rf"^/{settings.APP_PREFIX}/(?P<tenant_id>\w+)/admin/?", path)
        next_param = request.GET.get("next")

        if match:
            tenant_id = match.group("tenant_id")
            logger.info(f"[TenantMiddleware] Tenant ID from URL path: {tenant_id}")

        elif next_param:
            match = re.match(rf"^/{settings.APP_PREFIX}/(?P<tenant_id>\w+)/admin/?", next_param)
            if match:
                tenant_id = match.group("tenant_id")
                logger.info(f"[TenantMiddleware] Tenant ID from next param: {tenant_id}")

        elif hasattr(request, 'tenant_id'):
            logger.info(f"[TenantMiddleware] Skipping middleware: tenant already set to '{request.tenant_id}'")
            tenant_id = request.tenant_id
        else:
            tenant_id = request.headers.get("X-Tenant-ID")
            logger.info(f"[TenantMiddleware] Tenant ID from header: {tenant_id}")

        if not tenant_id:
            logger.info(f"[TenantMiddleware] No tenant ID in URL, next param, or headers. Using default.")
            tenant_id = self.default_tenant

        set_current_tenant(tenant_id)
        request.tenant_id = tenant_id
