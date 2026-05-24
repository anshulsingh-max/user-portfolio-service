"""
URL configuration for user_portfolio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path, URLPattern
from health_check.views import HealthCheckView

from multitenant.admin_site import tenant_admin_site


urlpatterns = [
    path(f'{settings.APP_PREFIX}/admin/', admin.site.urls),
    re_path(rf'^{settings.APP_PREFIX}/[^/]+/admin/', tenant_admin_site.urls),
    path(f'{settings.APP_PREFIX}/grappelli/', include('grappelli.urls')),
    path(f'{settings.APP_PREFIX}/holding/', include('apps.holdings.urls')),
    path(f'{settings.APP_PREFIX}/userportfolio/', include('apps.portfolio.urls')),
    # django-health-check 4.x removed its bundled urls.py; register the
    # view directly. Trailing slash preserved for backwards compatibility
    # with existing monitors.
    path(
        f'{settings.APP_PREFIX}/health_check/',
        HealthCheckView.as_view(),
        name='health_check',
    ),
]
if settings.ENABLE_METRICS:
    from django_prometheus import exports
    from middlewares.metrics_auth import basic_auth_required

    guarded_metrics_view = basic_auth_required(exports.ExportToDjangoView)
    urlpatterns += [path(f'{settings.APP_PREFIX}/metrics', guarded_metrics_view),
                    path(f'{settings.APP_PREFIX}/metrics/', guarded_metrics_view)]
