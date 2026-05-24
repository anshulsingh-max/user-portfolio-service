import re
import logging
from functools import wraps

from django.conf import settings
from django.contrib.admin import AdminSite
from django.urls import URLPattern, re_path

logger = logging.getLogger(__name__)


class TenantAdminSite(AdminSite):
    """
    Custom AdminSite that supports multi-tenant URL structures by extracting
    `tenant_id` from the URL and injecting it into the context.
    """

    def get_urls(self):
        """
        Returns a list of URL patterns for the admin site, wrapping each view
        to remove `tenant_id` from `kwargs` to avoid breaking admin views.

        Returns:
            List[URLPattern]: Modified list of URL patterns for tenant admin.
        """

        def wrap(view):
            @wraps(view)
            def inner(request, *args, **kwargs):
                removed = kwargs.pop('tenant_id', None)
                if removed:
                    logger.info(f"Removed tenant_id '{removed}' from kwargs in wrapped admin view.")
                return view(request, *args, **kwargs)

            return inner

        original_urls = super().get_urls()
        new_urls = []

        for url in original_urls:
            if isinstance(url, URLPattern):
                logger.info(f"Wrapping admin URL pattern: {url.name}")
                new_urls.append(
                    re_path(url.pattern.regex.pattern, wrap(url.callback), name=url.name)
                )
            else:
                logger.info("Appending unmodified URLResolver.")
                new_urls.append(url)

        return new_urls

    def each_context(self, request):
        """
        Adds `tenant_id` to the admin template context.

        Args:
            request (HttpRequest): The current HTTP request.

        Returns:
            dict: Context including `tenant_id`.
        """
        context = super().each_context(request)
        tenant_id = self.get_tenant_from_request(request)
        context['tenant_id'] = tenant_id
        logger.info(f"Injected tenant_id '{tenant_id}' into admin context.")
        return context

    def get_tenant_from_request(self, request):
        """
        Extracts `tenant_id` from the request URL path.

        Args:
            request (HttpRequest): The incoming request.

        Returns:
            str | None: The tenant ID if present in path, else None.
        """
        match = re.match(rf"^/{settings.APP_PREFIX}/(?P<tenant_id>[^/]+)/", request.path)
        if match:
            tenant_id = match.group("tenant_id")
            logger.info(f"Extracted tenant_id '{tenant_id}' from path '{request.path}'")
            return tenant_id
        logger.info(f"No tenant_id found in path '{request.path}'")
        return None

    def reverse(self, viewname, args=None, kwargs=None, current_app=None):
        """
        Overrides URL reversing to support tenant-specific routes.

        Args:
            viewname (str): The name of the view to reverse.
            args (list, optional): Positional arguments for the view.
            kwargs (dict, optional): Keyword arguments for the view.
            current_app (str, optional): Current app name.

        Returns:
            str: Reversed URL path.
        """
        logger.info(f"Reversing URL for view: {viewname}")
        return super().reverse(viewname, args=args, kwargs=kwargs, current_app=current_app)


# Instance to be used in admin.py or urls.py
tenant_admin_site = TenantAdminSite(name='tenant_admin')
