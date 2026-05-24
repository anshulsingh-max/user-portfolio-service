from __future__ import annotations

import logging

import pandas as pd
from bw_essentials.notifications.teams_notifications import Notifications
from bw_essentials.services.master_data import MasterData
from celery import shared_task
from django.conf import settings

from apps.alerts.constants import Status
from apps.alerts.models import HoldingThreshold, UserPortfolioThreshold
from apps.alerts.services.profit_stop_loss_monitor import AlertMonitoring
from apps.alerts.services.user_portfolio_threshold import get_active_thresholds, get_holdings_with_active_thresholds, \
    run_basket_pt_evaluation
from apps.portfolio.constants import BrokerEnum, NotificationEventsMTF
from apps.portfolio.models import UserPortfolio
from apps.utils.cache_lock import acquire_lock, release_lock
from apps.utils.prices import get_live_prices
from middlewares.constants import SERVICE, DOMAIN
from multitenant.tenant_context import set_current_tenant,get_current_tenant
pd.set_option('display.max_columns', None)
logger = logging.getLogger(__name__)
notification = Notifications(title=SERVICE)


def _resolve_and_activate_tenant(tenant_id: str | None) -> str:
    """
    Resolve tenant for the running task and activate thread-local tenant context.
    """
    resolved = tenant_id or 'default'
    if resolved not in settings.TENANTS:
        resolved='default'
    set_current_tenant(resolved)
    return resolved


@shared_task(bind=True, name=settings.SCHEDULER_PORTFOLIO_MONITORING)
def scheduler_portfolio_monitoring(self):
    for tenant_id in settings.TENANTS:
        scheduler_portfolio_monitoring_.delay(tenant_id=tenant_id)



@shared_task(bind=True, name=settings.SCHEDULER_PORTFOLIO_MONITORING_)
def scheduler_portfolio_monitoring_(self,tenant_id:str=None):
    """Parent task that schedules child monitoring tasks for all active portfolios."""
    tenant_activated=_resolve_and_activate_tenant(tenant_id=tenant_id)

    cache_key = settings.SCHEDULER_PORTFOLIO_MONITORING_ + tenant_activated
    if not MasterData(service_user=SERVICE).is_market_open(broker=BrokerEnum.HDFC.value,
                                                           domain=DOMAIN):
        logger.info("Market is closed. Skipping scheduler portfolio monitoring task.")
        return
    logger.info("Starting parent alert monitoring task with %s", cache_key)

    if acquire_lock(cache_key):
        try:
            basket_with_pt = run_basket_pt_evaluation()
            for basket in basket_with_pt.to_dict(orient='records'):
                user_portfolio_id = basket.get('threshold_portfolio_id')
                logger.info(f"Dispatching alert for {user_portfolio_id =}")
                monitor_portfolio_alerts.delay(user_portfolio_id=int(user_portfolio_id),tenant_id=tenant_id)
                logger.info(f"Triggered alert task for portfolio {user_portfolio_id}")
            logger.info("Triggered alert tasks for all active portfolios")
        except Exception as e:
            logger.error("Failed to evaluate portfolio alerts: %s", e)
            logger.exception(e)
            notification.notify_error(
                message=f"Error in scheduler_portfolio_monitoring {cache_key}",
                summary=str(e)
            )
        finally:
            release_lock(cache_key)
    else:
        logger.info("Another instance of %s task is already running. Skipping execution.", cache_key)


@shared_task(bind=True, name=settings.MONITOR_PORTFOLIO_ALERTS)
def monitor_portfolio_alerts(self, user_portfolio_id: int,tenant_id:str=None):
    """Child task that evaluates thresholds for a single user portfolio."""
    tenant_activated=_resolve_and_activate_tenant(tenant_id=tenant_id)
    cache_key = f"alert_monitoring_child_{user_portfolio_id}_{tenant_activated}"
    logger.info("Starting child alert monitoring task for portfolio %s", user_portfolio_id)
    if not MasterData(service_user=SERVICE).is_market_open(broker=BrokerEnum.HDFC.value,
                                                           domain=DOMAIN):
        logger.info("Market is closed. Skipping scheduler portfolio monitoring task.")
        return
    if acquire_lock(cache_key):
        user_portfolio_threshold = None
        try:
            user_portfolio_threshold = UserPortfolioThreshold.objects.get(portfolio_type='user_portfolio',
                                                                          portfolio_id=str(user_portfolio_id),
                                                                          status=Status.ACTIVE)
            logger.info("Found active threshold for portfolio %s", user_portfolio_id)
            user_portfolio = UserPortfolio.objects.get(id=user_portfolio_id)
            AlertMonitoring().handle_trigger(
                threshold=user_portfolio_threshold,
                user_id=user_portfolio.user_id,
                user_portfolio_id=user_portfolio_id,
                portfolio_id=user_portfolio.portfolio_id,
                event_name=NotificationEventsMTF.PROFIT_TARGET_HIT_1_MTF.value
            )
        except Exception as e:
            logger.info("Failed to evaluate portfolio threshold %s: %s", user_portfolio_threshold, e)
            logger.exception(e)
            notification.notify_error(
                message=f"Error in monitor_portfolio_alerts {cache_key}",
                summary=str(e)
            )
        finally:
            release_lock(cache_key)
    else:
        logger.info("Another instance of child task %s is already running. Skipping execution.", cache_key)

@shared_task(bind=True, name=settings.SCHEDULER_HOLDING_MONITORING)
def scheduler_holding_monitoring(self):
    for tenant_id in settings.TENANTS:
        scheduler_holding_monitoring_(tenant_id=tenant_id)

@shared_task(bind=True, name=settings.SCHEDULER_HOLDING_MONITORING_)
def scheduler_holding_monitoring_(self,tenant_id:str=None):
    """Parent task that schedules child monitoring tasks for all active holding thresholds."""
    tenant_activated=_resolve_and_activate_tenant(tenant_id=tenant_id)
    cache_key = settings.SCHEDULER_HOLDING_MONITORING_ + tenant_activated
    if not MasterData(service_user=SERVICE).is_market_open(broker=BrokerEnum.HDFC.value,
                                                           domain=DOMAIN):
        logger.info("Market is closed. Skipping scheduler holding monitoring task.")
        return
    logger.info("Starting parent alert monitoring task with %s", cache_key)

    if acquire_lock(cache_key):
        try:
            records = AlertMonitoring().get_active_symbols_with_thresholds()
            logger.info(f"Fetched {len(records)} active records with thresholds {tenant_activated}")
            for record in records:
                price_dict = get_live_prices(record['symbol'])
                record['live_price'] = price_dict.get('price')
            records_df = pd.DataFrame(records)
            if not records_df.empty:
                # checking for stop loss hit (target_value > live_price)
                records_df = records_df[records_df['stop_loss_price'] >= records_df['live_price']]
                logger.info(f"Fetched {len(records)} active records for tenant {tenant_activated} and {len(records_df)} records after stop loss hit filter")
                for record in records_df.to_dict(orient='records'):
                    logger.info(f'{record = } for tenant {tenant_activated}')
                    holding_threshold = HoldingThreshold.objects.filter(
                        holding_id=record['holding_id'],
                        status="active"
                    ).order_by('-created').first()
                    
                    if holding_threshold:
                        logger.info(f"Scheduling processing for threshold ID: {holding_threshold.id} (status remains {holding_threshold.status}) for tenant {tenant_activated}")
                        monitor_holding_threshold_alerts.delay(holding_threshold.id, record,tenant_id=tenant_id)
                    else:
                        logger.info(f"No active stop loss threshold found for holding_id: {record['holding_id']} for tenant {tenant_activated}")
                logger.info(f"Processed {len(records_df)} active records")
            else:
                logger.info(f"No active records found for tenant {tenant_activated}")
        except Exception as e:
            logger.info("Failed to evaluate holding threshold alerts for tenant %s: %s", tenant_activated, e)
            logger.exception(e)
            notification.notify_error(
                message=f"Error in scheduler_holding_monitoring {cache_key} for tenant {tenant_activated}",
                summary=str(e)
            )
        finally:
            release_lock(cache_key)
    else:
        logger.info("Another instance of %s task is already running. Skipping execution.", cache_key)


@shared_task(bind=True, name=settings.MONITOR_HOLDING_THRESHOLD_ALERTS)
def monitor_holding_threshold_alerts(self, threshold_id: int, record,tenant_id:str=None):
    """Child task that evaluates a single holding threshold."""
    tenant_activated=_resolve_and_activate_tenant(tenant_id=tenant_id)
    cache_key = f"{settings.MONITOR_HOLDING_THRESHOLD_ALERTS}_{threshold_id}_{tenant_activated}"
    logger.info("Starting child alert monitoring task for holding threshold %s: %s", threshold_id, record)
    if not MasterData(service_user=SERVICE).is_market_open(broker=BrokerEnum.HDFC.value,
                                                           domain=DOMAIN):
        logger.info("Market is closed. Skipping scheduler portfolio monitoring task.")
        return
    if acquire_lock(cache_key):
        holding_threshold = None
        try:
            holding_threshold = HoldingThreshold.objects.get(id=threshold_id)
            holding_threshold.status = Status.PROCESSING
            holding_threshold.save(update_fields=["status"])

            user_id = record.get("user_id")
            user_portfolio_id = record.get("user_portfolio_id")
            portfolio_id = record.get("portfolio_id")
            AlertMonitoring().handle_trigger(
                threshold=holding_threshold,
                user_id=user_id,
                user_portfolio_id=user_portfolio_id,
                portfolio_id=portfolio_id,
                event_name=NotificationEventsMTF.STOP_LOSS_HIT_MTF.value
            )
        except Exception as e:
            logger.info("Failed to evaluate holding threshold %s: %s", threshold_id, e)
            logger.exception(e)
            if holding_threshold is not None:
                holding_threshold.reason = f"error: {e}"
                holding_threshold.status = Status.ACTIVE
                holding_threshold.save(update_fields=["reason", "status"])
            notification.notify_error(
                message=f"Error in monitor_holding_threshold_alerts {cache_key}",
                summary=str(e)
            )
        finally:
            try:
                if holding_threshold is not None:
                    holding_threshold.status = Status.ACTIVE
                    holding_threshold.save(update_fields=["status"])
            finally:
                release_lock(cache_key)
    else:
        logger.info("Another instance of child task %s is already running. Skipping execution.", cache_key)
