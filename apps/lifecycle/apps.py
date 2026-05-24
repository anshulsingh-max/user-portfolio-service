"""Django app config for the lifecycle authority."""

from __future__ import annotations

from django.apps import AppConfig


class LifecycleConfig(AppConfig):
    """Lifecycle bounded context - TransitionService, CallbackLog, history."""

    name = "apps.lifecycle"
    label = "lifecycle"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "Lifecycle"
