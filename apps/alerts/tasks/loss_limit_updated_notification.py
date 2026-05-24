import logging
from datetime import datetime

from celery import shared_task
from django.conf import settings

from apps.portfolio.constants import ProductTypes
from apps.portfolio.models import UserPortfolio
from bw_essentials.EventNotification.EventBridgePublisher import EventBridgePublisher
from bw_essentials.EventNotification.NotificationType import NotificationType

from multitenant.tenant_context import set_current_tenant, resolve_set_tenant
from wrappers.portfolio_business import PortfolioBusiness

logger = logging.getLogger(__name__)


@shared_task(bind=True, name=settings.SEND_LOSS_LIMIT_UPDATED_NOTIFICATION)
def send_loss_limit_updated_notification(self, user_portfolio_id: int, loss_limit: float | None = None,tenant_id: str | None = None):
    """
    Fire a loss limit updated notification event for a user portfolio.

    This task publishes a notification event to EventBridge with no explicit retry or locking
    mechanisms. Retries are not configured because this is a best-effort notification delivery
    where failures are logged but do not impact core business logic. Each task instance operates
    independently on a single user portfolio record, eliminating the need for distributed locks.
    """
    logger.info('Checking loss limit update notification for user portfolio id %s', user_portfolio_id)
    resolve_set_tenant(tenant_id)
    try:
        user_portfolio = UserPortfolio.objects.get(id=user_portfolio_id)
        pb = PortfolioBusiness()
        if user_portfolio.product_type == ProductTypes.MTF.value:
            portfolio_data = pb.active_model_by_id(user_portfolio.portfolio_id, user_portfolio.broker)
            portfolio_data = portfolio_data.get('content', {})
        else:
            portfolio_data = pb.portfolio_details(user_portfolio.portfolio_id)
            portfolio_data = portfolio_data.get('portfolio', {})
            logger.info(f"Portfolio details fetched: {portfolio_data}")
        basket_name = portfolio_data.get('name', user_portfolio.portfolio_id)
    except Exception as e:
        logger.info("UserPortfolio not found for user_portfolio_id=%s", user_portfolio_id)
        return

    stop_loss_limit = loss_limit

    if stop_loss_limit is None:
        logger.info(
            "No active stop loss limit found for user_portfolio_id=%s; defaulting to 0.0",
            user_portfolio_id,
        )
        stop_loss_limit = 0.0

    start_date_str=datetime.now().isoformat()

    notification = NotificationType()
    event = notification.loss_alert_updated(
        user_id=user_portfolio.user_id,
        basket_name=basket_name,
        start_date=start_date_str,
        stop_loss_limit=stop_loss_limit,
        broker_name=user_portfolio.broker,
        product=user_portfolio.product_type,
        platform="youtrade",
        user_name=user_portfolio.name
    )
    event["data"]["user_portfolio_id"] = user_portfolio_id


    publisher = EventBridgePublisher()
    publisher.send_event_notification(event, source="user-event")
    logger.info(
        "Published loss limit updated notification for user_portfolio_id=%s",
        user_portfolio_id,
    )
