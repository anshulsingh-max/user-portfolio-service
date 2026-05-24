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
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework_swagger.views import get_swagger_view

from multitenant.admin_site import tenant_admin_site
from user_portfolio.swagger import HttpAndHttpsSchemaGenerator

schema_view = get_swagger_view(title='Pastebin API')

SchemaView = get_schema_view(
    openapi.Info(
      title="Snippets API",
      default_version='0.0.2',
      description="Swagger APIs",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
    ),
    public=True,
    generator_class=HttpAndHttpsSchemaGenerator,
    url=settings.BASE_URL
)


urlpatterns = [
    path(f'{settings.APP_PREFIX}/admin/', admin.site.urls),
    re_path(rf'^{settings.APP_PREFIX}/[^/]+/admin/', tenant_admin_site.urls),
    path(f'{settings.APP_PREFIX}/grappelli/', include('grappelli.urls')),
    path(f'{settings.APP_PREFIX}/holding/', include('apps.holdings.urls')),
    path(f'{settings.APP_PREFIX}/userportfolio/', include('apps.portfolio.urls')),
    path(f'{settings.APP_PREFIX}/health_check/', include('health_check.urls')),
    # path(f'{settings.APP_PREFIX}/swagger/', SchemaView.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # re_path(f'{settings.APP_PREFIX}/redoc/', SchemaView.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
if settings.ENABLE_METRICS:
    from django_prometheus import exports
    from middlewares.metrics_auth import basic_auth_required

    guarded_metrics_view = basic_auth_required(exports.ExportToDjangoView)
    urlpatterns += [path(f'{settings.APP_PREFIX}/metrics', guarded_metrics_view),
                    path(f'{settings.APP_PREFIX}/metrics/', guarded_metrics_view)]
