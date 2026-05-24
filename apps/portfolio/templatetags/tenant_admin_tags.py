import logging
import re
from urllib.parse import unquote

from django import template
from django.contrib.admin.templatetags.admin_list import result_list
from django.urls import reverse

logger = logging.getLogger(__name__)

register = template.Library()


@register.simple_tag(takes_context=True)
def tenant_admin_url(context, viewname, *args, **kwargs):
    tenant_id = context.get("tenant_id")
    logger.info(f"Generating admin URL for tenant_id={tenant_id}, viewname={viewname}, args={args}, kwargs={kwargs}")
    url = reverse(viewname, args=args, kwargs=kwargs)
    logger.info(f"Initial reversed URL: {url}")
    if tenant_id:
        parts = url.split("/")
        parts.insert(2, tenant_id)
        url = "/".join(parts)
        logger.info(f"Tenant-specific URL: {url}")
    return url


@register.simple_tag(takes_context=True)
def inject_tenant(context, url):
    tenant_id = context.get("tenant_id")
    original_url = url
    url = unquote(url)
    url = url.replace('/^', '')

    logger.info(f"Injecting tenant into URL: original={original_url}, unquoted={url}, tenant_id={tenant_id}")

    if tenant_id:
        parts = url.split("/")
        parts.insert(2, tenant_id)
        url = "/".join(parts)
        logger.info(f"Tenant-injected URL: {url}")
    return url


@register.filter
def change_href(item, tenant_id):
    logger.info(f"Modifying href for tenant_id={tenant_id}")
    match = re.search(r'href="([^"]+)"', item)
    if match:
        url = match.group(1)
        unquote_url = unquote(url).replace('/^', '')
        logger.info(f"Original href: {url}, Unquoted and cleaned: {unquote_url}")
        if tenant_id:
            parts = unquote_url.split("/")
            parts.insert(2, tenant_id)
            href = "/".join(parts)
        else:
            href = url
        logger.info(f"Updated href: {href}")
        item = item.replace(url, href)
    return item


@register.inclusion_tag("admin/change_list_results.html", takes_context=True)
def tenant_result_list(context, cl):
    tenant_id = context.get("tenant_id")
    logger.info(f"Rendering tenant result list for tenant_id={tenant_id}")
    rendered = result_list(cl)
    rendered["tenant_id"] = tenant_id
    return rendered


@register.simple_tag(takes_context=True)
def base_url(context, viewname, *args, **kwargs):
    tenant_id = context.get("tenant_id")
    logger.info(f"Generating admin URL for tenant_id={tenant_id}, viewname={viewname}, args={args}, kwargs={kwargs}")
    url = reverse(viewname, args=args, kwargs=kwargs)
    logger.info(f"Initial reversed URL: {url}")
    if tenant_id:
        parts = url.split("/")
        # parts.insert(2, tenant_id)
        url = "/".join(parts)
        logger.info(f"Tenant-specific URL: {url}")
    return url
