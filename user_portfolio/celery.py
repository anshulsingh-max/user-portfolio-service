from __future__ import absolute_import, unicode_literals

from logging.config import dictConfig

from celery import Celery
import os

from celery.signals import setup_logging
from django.conf import settings

from configurations.base import celery_log_config

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "configurations.local")

celery_app = Celery(settings.APP_NAME)
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
celery_app.config_from_object("django.conf:settings")

# Load task modules from all registered Django app config.
celery_app.autodiscover_tasks()


@setup_logging.connect
def setup_logging(**_kwargs):
    dictConfig(celery_log_config)
