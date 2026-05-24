"""
    Cache utility file
"""
import logging
import time
from bw_essentials.notifications.teams_notifications import Notifications
from middlewares.constants import SERVICE
from django.core.cache import cache

logger = logging.getLogger(__name__)

notification = Notifications(title=SERVICE)

def acquire_lock(lock_key, lock_expire=300):
    # pylint: disable=broad-except
    """
        Acquire task lock function
        :param lock_key: string to take lock on
        :param lock_expire: expiry time for lock
        :return: Boolean
    """
    try:
        return cache.add(lock_key, '1', lock_expire)
    except Exception as exc:
        logger.exception(exc)
        return False


def release_lock(lock_key):
    # pylint: disable=broad-except
    """
        Release task lock function
        :param lock_key: string to take lock on
        :return: Boolean
    """
    try:
        return cache.delete(lock_key)
    except Exception as exc:
        logger.exception(exc)
        return False


def acquire_lock_retry(lock_key, lock_expire=300, max_attempts=10, notification_threshold=5):
    attempts = 0
    got_lock = False

    while attempts < max_attempts:
        if acquire_lock(lock_key, lock_expire):
            got_lock = True
            break
        sleep_sec = 1 if attempts < notification_threshold else 5
        time.sleep(sleep_sec)
        attempts += 1

        if sleep_sec == 5:
            notification.notify_error(message=f"Could not acquire lock {lock_key}, retried for {attempts} times")

    return got_lock