"""
tasks/monitoring.py

This module contains Celery tasks for monitoring investment baskets and orders. The tasks handle
profit target checks, stop-loss monitoring, and ensure no overlapping execution through cache locks.

Tasks:
    - monitoring: Monitors all baskets in the "MONITORING" state and triggers basket and order monitoring tasks.
    - monitor_basket: Checks and updates the profit targets for a specific basket.
    - monitor_orders: Checks and updates the stop-loss for a specific order.

Dependencies:
    - Celery shared tasks
    - Django ORM for querying baskets and orders
    - Notification service for sending alerts
    - Cache locking mechanism to prevent simultaneous task execution
"""

import logging

from bw_essentials.services.master_data import MasterData
from celery import shared_task
from django.conf import settings
from apps.portfolio.constants import BasketStates, BrokerEnum
from apps.portfolio.models import Basket
from apps.portfolio.services.profit_stop_loss_monitor import ProfitStopLossMonitor
from apps.utils.cache_lock import acquire_lock, release_lock
from apps.utils.notifications import Notifications
from middlewares.constants import SERVICE, DOMAIN
from multitenant.tenant_context import set_current_tenant

logger = logging.getLogger(__name__)
notification = Notifications(title=SERVICE)


def _resolve_and_activate_tenant(tenant_id=None):
    resolved = tenant_id or 'default'
    if resolved not in settings.TENANTS:
        resolved = 'default'
    set_current_tenant(resolved)
    return resolved


@shared_task(bind=True, name=settings.MONITORING)
def monitoring(self, tenant_id=None):
    """
    Main task to monitor all baskets in the "MONITORING" state.
    For each basket, triggers tasks to monitor the basket itself and its associated orders.

    Args:
        self: The task instance (provided by Celery).

    Raises:
        Exception: If an error occurs during monitoring, it is logged and re-raised.
    """
    if tenant_id is None:
        for tenant in settings.TENANTS:
            monitoring.delay(tenant_id=tenant)
        return

    tenant_activated = _resolve_and_activate_tenant(tenant_id)
    cache_key = f"{settings.MONITORING}_{tenant_activated}"
    logger.info(f"Starting monitoring task with {cache_key = }")
    if not MasterData(service_user=SERVICE).is_market_open(broker=BrokerEnum.HDFC.value,
                                                           domain=DOMAIN):
        logger.info("Market is closed. Skipping monitoring task.")
        return
    if acquire_lock(cache_key):
        try:
            baskets = Basket.objects.filter(current_state=BasketStates.MONITORING.value)
            logger.info(f"Found {len(baskets)} baskets to monitor.")

            for basket in baskets:
                logger.info(f"Scheduling monitor tasks for Basket ID: {basket.id}")
                monitor_basket.delay(basket.id, tenant_id=tenant_activated)
                for order in basket.user_basket.all():
                    logger.info(f"Scheduling monitor task for Order ID: {order.id} (Basket ID: {basket.id})")
                    monitor_orders.delay(order.id, tenant_id=tenant_activated)

        except Exception as exc:
            logger.error(f"Error in monitoring task: {exc}")
            logger.exception(exc)
            notification.notify_error(
                message=f"Error in monitoring task {cache_key}",
                summary=str(exc)
            )
            raise exc
        finally:
            logger.info(f"Releasing lock for {cache_key = }")
            release_lock(cache_key)
    else:
        logger.info(f"Another monitoring task is already running for {cache_key = }. Skipping this execution.")


@shared_task(bind=True, name=settings.MONITOR_BASKET)
def monitor_basket(self, basket_id, tenant_id=None):
    """
    Task to monitor a specific basket and check its profit targets.

    Args:
        self: The task instance (provided by Celery).
        basket_id: ID of the basket to monitor.

    Raises:
        Exception: If an error occurs during basket monitoring, it is logged and re-raised.
    """
    tenant_activated = _resolve_and_activate_tenant(tenant_id)
    cache_key = f"{settings.MONITOR_BASKET}_{basket_id}_{tenant_activated}"
    logger.info(f"Starting monitor_basket task for {cache_key = }")

    if acquire_lock(cache_key):
        try:
            logger.info(f"Checking profit targets for Basket ID: {basket_id}")
            ProfitStopLossMonitor().check_profit_target(basket_id)
        except Exception as exc:
            logger.error(f"Error in monitor_basket task for Basket ID {basket_id}: {exc}")
            logger.exception(exc)
            notification.notify_error(
                message=f"Error in basket monitoring task {cache_key}",
                summary=str(exc)
            )
            raise exc
        finally:
            logger.info(f"Releasing lock for {cache_key = }")
            release_lock(cache_key)
    else:
        logger.info(f"Another monitor_basket task is already running for {cache_key = }. Skipping this execution.")


@shared_task(bind=True, name=settings.MONITOR_ORDER)
def monitor_orders(self, order_id, tenant_id=None):
    """
    Task to monitor a specific order and check its stop-loss.

    Args:
        self: The task instance (provided by Celery).
        order_id: ID of the order to monitor.

    Raises:
        Exception: If an error occurs during order monitoring, it is logged and re-raised.
    """
    tenant_activated = _resolve_and_activate_tenant(tenant_id)
    cache_key = f"{settings.MONITOR_ORDER}_{order_id}_{tenant_activated}"
    logger.info(f"Starting monitor_orders task for {cache_key = }")

    if acquire_lock(cache_key):
        try:
            logger.info(f"Checking stop-loss for Order ID: {order_id}")
            ProfitStopLossMonitor().check_stop_loss(order_id)
        except Exception as exc:
            logger.error(f"Error in monitor_orders task for Order ID {order_id}: {exc}")
            logger.exception(exc)
            notification.notify_error(
                message=f"Error in order monitoring task {cache_key}",
                summary=str(exc)
            )
            raise exc
        finally:
            logger.info(f"Releasing lock for {cache_key = }")
            release_lock(cache_key)
    else:
        logger.info(f"Another monitor_orders task is already running for {cache_key = }. Skipping this execution.")
