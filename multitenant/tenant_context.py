import threading
import logging
from urllib.parse import unquote

from django.conf import settings

logger = logging.getLogger(__name__)

_thread_locals = threading.local()


def set_current_tenant(tenant_id):
    """
    Stores the current tenant ID in thread-local storage.

    Args:
        tenant_id (str): The tenant identifier to set.
    """
    _thread_locals.tenant_id = tenant_id
    logger.debug(f"[tenant_context] Set tenant to: {tenant_id}")


def get_current_tenant():
    """
    Retrieves the current tenant ID from thread-local storage.

    Returns:
        str or None: The current tenant identifier, or None if not set.
    """
    tenant = getattr(_thread_locals, 'tenant_id', None)
    logger.debug(f"[tenant_context] Get tenant: {tenant}")
    return tenant


def tenant_selector(request):
    """
    Provides tenant-related context for templates.

    Args:
        request: Django HTTP request object.

    Returns:
        dict: Dictionary with available tenants, current tenant, and app prefix.
    """
    current_tenant = getattr(request, 'tenant', None)
    logger.debug(f"[tenant_context] tenant_selector: current tenant from request = {current_tenant}")
    return {
        'tenants': settings.TENANTS,
        'current_tenant': current_tenant,
        'app_prefix': settings.APP_PREFIX
    }


def inject_tenant(url, tenant_id):
    """
    Injects tenant ID into the provided URL by replacing the ^ symbol.

    Args:
        url (str): The URL pattern containing '^' as placeholder.
        tenant_id (str): The tenant ID to inject.

    Returns:
        str: Updated URL with tenant ID injected.
    """
    original_url = url
    unquote_url = unquote(url)

    if tenant_id:
        unquote_url = unquote_url.replace('^', tenant_id)
        logger.debug(f"[tenant_context] inject_tenant: Injected tenant_id='{tenant_id}' into URL. Original: '{original_url}', Updated: '{unquote_url}'")
    else:
        unquote_url = unquote_url.replace('^', "default")
        logger.debug(f"[tenant_context] inject_tenant: No tenant_id provided, using 'default'. Original: '{original_url}', Updated: '{unquote_url}'")

    return unquote_url

def resolve_set_tenant(tenant_id):
    """
    Resolves and sets the tenant ID in thread-local storage.

    Args:
        tenant_id (str): The tenant identifier to resolve and set.
    """
    if tenant_id in settings.TENANTS:
        set_current_tenant(tenant_id)
        logger.debug(f"[tenant_context] resolve_set_tenant: Resolved and set tenant_id='{tenant_id}'")
    else:
        set_current_tenant('default')
        logger.warning(f"[tenant_context] resolve_set_tenant: Invalid tenant_id='{tenant_id}' provided. Set to 'default'.")