"""
    Command to populate trading symbols in broker data
"""
import logging
import time

from bw_essentials.services.master_data import MasterData
from django.core.cache import cache
from django.core.management.base import BaseCommand

from apps.alerts.constants import ACTIVE_PORTFOLIOS_CACHE_KEY, ACTIVE_HOLDINGS_THRESHOLD_CACHE_KEY, HOLDINGS_CACHE_KEY
from apps.alerts.tasks import scheduler_portfolio_monitoring
from apps.alerts.tasks.profit_stop_loss_monitoring import scheduler_holding_monitoring
from apps.portfolio.constants import BrokerEnum
# from apps.alerts.services.alert_monitoring import AlertMonitoring
from apps.portfolio.services.user_portfolio import get_event_details
from middlewares.constants import SERVICE, DOMAIN

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Class of command
    """

    def handle(self, *args, **options):
        scheduler_portfolio_monitoring()
        # scheduler_holding_monitoring()
        # logger.info("starting scheduler_holding_monitoring")
        # while True:
        #     scheduler_holding_monitoring()
        #     logger.info("Sleeping for seconds...")
        #     time.sleep(5)
