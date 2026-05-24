import logging

from celery import shared_task
from django.conf import settings

from apps.portfolio.services.user_instruction import business_rebalance_sell_callback
from apps.utils.cache_lock import acquire_lock, release_lock
from apps.utils.notifications import Notifications
from middlewares.constants import SERVICE
from multitenant.tenant_context import set_current_tenant

logger = logging.getLogger(__name__)


@shared_task(bind=True, name=settings.PHASE_DETAIL_CALLBACK)
def phase_detail_callback(self, user_portfolio_rebalance_id, tenant_id=None, rebalance_transaction_id=None, retry=False):
    """
    Celery task to notify the rebalance business service about the completion
    of the sell phase details for a given user portfolio rebalance.

    This task is triggered (e.g., via signal) after a SELL-side `UserInstruction`
    is marked as FILLED. It ensures that the callback is processed for the correct
    tenant by explicitly setting the tenant context.

    Args:
        self (Task): The current Celery task instance.
        user_portfolio_rebalance_id (int): The ID of the user portfolio rebalance record.
        tenant_id (str, optional): The tenant identifier used to route the database operations.
                                   If not provided, the task may default to the wrong DB.
        rebalance_transaction_id: The ID of the rebalance transaction record.
        retry (bool, optional): Flag to indicate if this task is being retried. Used in task_id for deduplication/logging.

    Notes:
        - A lock is acquired before execution to prevent concurrent tasks on the same rebalance ID.
        - If tenant_id is not provided, task logs a warning and may fall back to default DB.
        - Exceptions during callback are caught and notified using the notification system.
    """
    task_id = f"{settings.PHASE_DETAIL_CALLBACK}_{user_portfolio_rebalance_id}_retry-{retry}"
    logger.info(f"Starting phase_detail_callback with {task_id = }")

    if tenant_id:
        set_current_tenant(tenant_id)
        logger.info(f"[phase_detail_callback] Tenant context set to: {tenant_id}")
    else:
        logger.info("[phase_detail_callback] No tenant_id provided, using default tenant DB.")

    if acquire_lock(task_id):
        logger.info(f"Acquired lock for task {task_id}")
        try:
            logger.info(f"Invoking business_rebalance_sell_callback for {user_portfolio_rebalance_id = }")
            business_rebalance_sell_callback(user_portfolio_rebalance_id, rebalance_transaction_id)
        except Exception as exc:
            logger.exception(f"Exception occurred during callback for {user_portfolio_rebalance_id = }: {exc}")
            Notifications(title=SERVICE).notify_error(
                message=f"Error in task {task_id}",
                summary=str(exc)
            )
        finally:
            logger.info(f"Releasing lock for task {task_id}")
            release_lock(task_id)
    else:
        logger.info(f"Other task is running for same {task_id = }, skipping this task")

