import logging

from celery import shared_task
from django.conf import settings
from django.db.models import Sum, Count, FloatField
from django.db.models.functions import Coalesce

from apps.portfolio.models import UserInstruction, UserPortfolioRebalance
from apps.portfolio.constants import OrderStatus, RebalanceTypes, CashTransaction, ProductTypes

from apps.utils.notifications import Notifications
from middlewares.constants import SERVICE
from multitenant.tenant_context import set_current_tenant
from bw_essentials.services.user_app import PrometheusUserApp
from bw_essentials.EventNotification.NotificationType import NotificationType
from bw_essentials.EventNotification.EventBridgePublisher import EventBridgePublisher
from bw_essentials.services.job_scheduler import JobScheduler
from datetime import datetime, timezone

from wrappers.portfolio_business import PortfolioBusiness

logger = logging.getLogger(__name__)


def sync_with_job_scheduler(user_portfolio,upr, tenant_id):
    """
    Syncs the task with the Job Scheduler to ensure it's registered and scheduled correctly.
    """
    job_scheduler = JobScheduler(SERVICE, tenant_id)

    logger.info(
        "Triggering user portfolio sync via JobScheduler in Monitor_User_Instruction| user_portfolio_id=%s | tenant_id=%s | broker=%s",
        upr.user_portfolio_id,
        tenant_id,
        user_portfolio.broker,
    )

    job_scheduler.sync_all_user_portfolios(user_portfolio_ids=[upr.user_portfolio_id])

    logger.info(
        "User portfolio sync triggered successfully Monitor_User_Instruction | user_portfolio_id=%s | tenant_id=%s | broker=%s",
        upr.user_portfolio_id,
        tenant_id,
        user_portfolio.broker,
    )


@shared_task(bind=True, name=settings.SEND_INVESTMENT_SUCCEEDED_EVENT, max_retries=3)
def send_investment_succeeded_event(
    self,
    user_portfolio_rebalance_id,
    tenant_id=None,
):
    """
    Sends an 'Investment Succeeded' notification when an INITIAL rebalance
    completes with some invested amount.

    Triggered by update_rebalance_state() via signal chain — no polling needed.
    """
    logger.info(
        f"send_investment_succeeded_event: rebalance_id={user_portfolio_rebalance_id}, tenant={tenant_id}"
    )

    if tenant_id:
        set_current_tenant(tenant_id)

    try:
        logger.info(f"Fetching rebalance data for id={user_portfolio_rebalance_id}")
        upr = UserPortfolioRebalance.objects.select_related('user_portfolio').get(
            id=user_portfolio_rebalance_id
        )
        user_portfolio = upr.user_portfolio
        logger.info(
            f"Rebalance found: type={upr.type}, transaction_type={upr.transaction_type}, "
            f"user_id={user_portfolio.user_id}, portfolio_id={user_portfolio.portfolio_id}, "
            f"product_type={user_portfolio.product_type}"
        )

        # Guard: only process INITIAL + ADD rebalances
        if upr.type != RebalanceTypes.INITIAL.value:
            logger.info(
                f"Skipping: rebalance type is {upr.type}, expected {RebalanceTypes.INITIAL.value}"
            )
            return
        if upr.transaction_type != CashTransaction.ADD.value:
            logger.info(
                f"Skipping: transaction_type is {upr.transaction_type}, expected {CashTransaction.ADD.value}"
            )
            return

        # Get filled instructions and calculate transaction amount
        agg = UserInstruction.objects.filter(
            portfolio_rebalance_transaction__portfolio_rebalance_id=user_portfolio_rebalance_id,
            status=OrderStatus.FILLED.value,
        ).aggregate(
            filled_count=Count('id'),
            transaction_amount=Coalesce(Sum('value'), 0, output_field=FloatField()),
        )
        filled_count = agg['filled_count']
        transaction_amount = agg['transaction_amount']
        logger.info(
            f"Filled instructions: count={filled_count}, transaction_amount={transaction_amount}"
        )

        if transaction_amount <= 0:
            logger.info(
                f"No invested amount for rebalance {user_portfolio_rebalance_id}, skipping notification"
            )
            return

        # Get user details
        logger.info(f"Fetching user details for user_id={user_portfolio.user_id}")
        user_app = PrometheusUserApp(service_user="user-portfolio-service", tenant_id=tenant_id)
        user_details = user_app.get_user_details(user_portfolio.user_id)
        phone_number = user_details.get('mobile') if user_details else None
        logger.info(f"User details fetched: phone_number={phone_number}")

        portfolio_business = PortfolioBusiness()
        if user_portfolio.product_type == ProductTypes.MTF.value:
            portfolio_data = portfolio_business.active_model_by_id(user_portfolio.portfolio_id, user_portfolio.broker)
            portfolio_data = portfolio_data.get('content', {})
        else:
            portfolio_data = portfolio_business.portfolio_details(user_portfolio.portfolio_id)
            portfolio_data = portfolio_data.get('portfolio', {})
            logger.info(f"Portfolio details fetched: {portfolio_data}")
        basket_name = portfolio_data.get('name', user_portfolio.portfolio_id)

        # Create investment successful event
        logger.info("Building investment_successful event payload")
        notification = NotificationType()
        event = notification.investment_successful(
            user_id=user_portfolio.user_id,
            phone_number=phone_number,
            basket_name=basket_name,
            basket_fee=0,
            transaction_amount=transaction_amount,
            investment_amount=transaction_amount,
            broker_name=user_portfolio.broker,
            product=user_portfolio.product_type,
            platform="youtrade",
            event_time=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            basket_type='free' if 'free' in user_portfolio.subscription_id else 'paid',
            basket_strategy=user_portfolio.strategy,
            user_name=user_portfolio.name,
        )
        logger.info(f"Event payload built: {event}")

        sync_with_job_scheduler(user_portfolio,upr, tenant_id)

        # Publish to EventBridge
        if event:
            logger.info("Publishing event to EventBridge")
            publisher = EventBridgePublisher()
            publisher.send_event_notification(event, source='user-event')
            logger.info("Event published to EventBridge successfully")
        else:
            logger.warning("Event payload is empty, skipping EventBridge publish")

        logger.info(
            f"Investment succeeded notification completed for rebalance {user_portfolio_rebalance_id}"
        )

    except Exception as e:
        logger.exception(
            f"Error sending investment succeeded notification for rebalance "
            f"{user_portfolio_rebalance_id}: {e}"
        )
        Notifications(title=SERVICE).notify_error(
            message="Error sending investment succeeded notification",
            summary=f"Rebalance {user_portfolio_rebalance_id}: {str(e)}",
        )
        self.retry(countdown=30, exc=e)


@shared_task(bind=True, name=settings.SEND_WITHDRAWAL_SUCCEEDED_EVENT, max_retries=3)
def send_withdrawal_succeeded_event(
    self,
    user_portfolio_rebalance_id,
    tenant_id=None,
):
    """
    Sends a 'Withdrawal Succeeded' notification when an INITIAL rebalance
    completes a withdrawal with some transaction amount.

    Triggered similarly to send_investment_succeeded_event — no polling needed.
    """
    logger.info(
        f"send_withdrawal_succeeded_event: rebalance_id={user_portfolio_rebalance_id}, tenant={tenant_id}"
    )

    if tenant_id:
        set_current_tenant(tenant_id)

    try:
        logger.info(f"Fetching rebalance data for id={user_portfolio_rebalance_id}")
        upr = UserPortfolioRebalance.objects.select_related('user_portfolio').get(
            id=user_portfolio_rebalance_id
        )
        user_portfolio = upr.user_portfolio
        logger.info(
            f"Rebalance found: type={upr.type}, transaction_type={upr.transaction_type}, "
            f"user_id={user_portfolio.user_id}, portfolio_id={user_portfolio.portfolio_id}, "
            f"product_type={user_portfolio.product_type}"
        )


        # Get filled instructions and calculate transaction amount
        agg = UserInstruction.objects.filter(
            portfolio_rebalance_transaction__portfolio_rebalance_id=user_portfolio_rebalance_id,
            status=OrderStatus.FILLED.value,
        ).aggregate(
            filled_count=Count('id'),
            transaction_amount=Coalesce(Sum('value'), 0, output_field=FloatField()),
        )
        filled_count = agg['filled_count']
        transaction_amount = agg['transaction_amount']
        logger.info(
            f"Filled instructions: count={filled_count}, transaction_amount={transaction_amount}"
        )

        if transaction_amount <= 0:
            logger.info(
                f"No withdrawal amount for rebalance {user_portfolio_rebalance_id}, skipping notification"
            )
            return

        # Get user details
        logger.info(f"Fetching user details for user_id={user_portfolio.user_id}")
        user_app = PrometheusUserApp(service_user="user-portfolio-service", tenant_id=tenant_id)
        user_details = user_app.get_user_details(user_portfolio.user_id)
        phone_number = user_details.get('mobile') if user_details else None
        logger.info(f"User details fetched: phone_number={phone_number}")

        portfolio_business=PortfolioBusiness()
        if user_portfolio.product_type==ProductTypes.MTF.value:
            portfolio_data=portfolio_business.active_model_by_id(user_portfolio.portfolio_id,user_portfolio.broker)
            portfolio_data=portfolio_data.get('content',{})
        else:
            portfolio_data=portfolio_business.portfolio_details(user_portfolio.portfolio_id)
            portfolio_data=portfolio_data.get('portfolio',{})
            logger.info(f"Portfolio details fetched: {portfolio_data}")
        basket_name=portfolio_data.get('name',user_portfolio.portfolio_id)

        # Create withdrawal successful event
        logger.info("Building withdrawal_successful event payload")
        notification = NotificationType()
        event = notification.withdrawal_successful(
            user_id=user_portfolio.user_id,
            phone_number=phone_number,
            basket_name=basket_name,
            sell_trade_value=transaction_amount,
            broker_name=user_portfolio.broker,
            product=user_portfolio.product_type,
            platform="youtrade",

            user_name=user_portfolio.name,
        )
        logger.info(f"Event payload built: {event}")

        sync_with_job_scheduler(user_portfolio,upr, tenant_id)

        # Publish to EventBridge
        if event:
            logger.info("Publishing event to EventBridge")
            publisher = EventBridgePublisher()
            publisher.send_event_notification(event, source='user-event')
            logger.info("Event published to EventBridge successfully")
        else:
            logger.warning("Event payload is empty, skipping EventBridge publish")

        logger.info(
            f"Withdrawal succeeded notification completed for rebalance {user_portfolio_rebalance_id}"
        )

    except Exception as e:
        logger.exception(
            f"Error sending withdrawal succeeded notification for rebalance "
            f"{user_portfolio_rebalance_id}: {e}"
        )
        Notifications(title=SERVICE).notify_error(
            message="Error sending withdrawal succeeded notification",
            summary=f"Rebalance {user_portfolio_rebalance_id}: {str(e)}",
        )
        self.retry(countdown=30, exc=e)
