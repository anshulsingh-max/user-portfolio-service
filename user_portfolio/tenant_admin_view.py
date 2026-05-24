from functools import wraps

from django.http import HttpRequest
from django.urls import URLResolver, URLPattern, path


def wrap_admin_urls(admin_site):
    def wrap(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            kwargs.pop('tenant_id', None)
            return view(request, *args, **kwargs)
        return wrapper

    def _wrap_urlpatterns(urlpatterns):
        wrapped = []
        for entry in urlpatterns:
            if isinstance(entry, URLPattern):
                # Get the pattern string safely (whether it's a RoutePattern or RegexPattern)
                route = getattr(entry.pattern, '_route', None)
                if route is None:
                    route = entry.pattern.regex.pattern.lstrip('^').rstrip('$')
                wrapped.append(
                    path(route, wrap(entry.callback), name=entry.name)
                )
            elif isinstance(entry, URLResolver):
                wrapped.append(
                    URLResolver(
                        entry.pattern,
                        _wrap_urlpatterns(entry.url_patterns),
                        entry.app_name,
                        entry.namespace,
                    )
                )
        return wrapped

    return _wrap_urlpatterns(admin_site.get_urls())


def strip_tenant_kwargs(view_func):
    def wrapper(request: HttpRequest, *args, **kwargs):
        kwargs.pop('tenant_id', None)  # Remove tenant_id
        return view_func(request, *args, **kwargs)
    return wrapper