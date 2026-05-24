import logging
import time
from datetime import timedelta

import pandas as pd
from bw_essentials.services.master_data import MasterData
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import OuterRef, Subquery, FloatField, IntegerField, CharField, Exists
from django.db.models.functions import Cast

from apps.alerts.tasks import monitor_portfolio_alerts, scheduler_portfolio_monitoring
from apps.portfolio.models import UserPortfolio
from apps.portfolio.constants import USER_PORTFOLIO, BrokerEnum
from apps.alerts.models import UserPortfolioThreshold
from apps.holdings.models import Holding
from apps.utils.prices import get_live_price_nse
from middlewares.constants import SERVICE, DOMAIN
from wrappers.market_pricer import MarketPricer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch active user portfolios with holdings and thresholds efficiently"

    def handle(self, *args, **options):

        while True:
            scheduler_portfolio_monitoring()
            time.sleep(10)

        while True:
            start_time = time.time()

            three_hours_ago = timezone.now() - timedelta(hours=3)
            thresholds_qs = (
                UserPortfolioThreshold.objects
                .filter(
                    status='active',
                    last_notification_sent_at__lte=three_hours_ago,
                )
                .annotate(pid_int=Cast('portfolio_id', IntegerField()))
            )
            holdings_qs = (
                Holding.objects
                .filter(
                    quantity__gt=0,
                )
                .annotate(
                    has_threshold=Exists(
                        thresholds_qs.filter(pid_int=OuterRef('user_portfolio_id'))
                    ),
                    target_pct=Subquery(
                        thresholds_qs.filter(pid_int=OuterRef('user_portfolio_id')).values('target_pct')[:1],
                        output_field=FloatField(),
                    ),
                    threshold_portfolio_id=Subquery(
                        thresholds_qs.filter(pid_int=OuterRef('user_portfolio_id')).values('portfolio_id')[:1],
                        output_field=CharField(),
                    ),
                )
                .filter(has_threshold=True)
                .values(
                    'threshold_portfolio_id',  # upt.portfolio_id (string)
                    # 'target_pct',              # upt.target_pct
                    # 'symbol',                  # h.symbol
                    # 'quantity',                # h.quantity
                    # 'avg_buy_price',           # h.avg_buy_price
                )
            )

            results_list = list(holdings_qs)
            # results_df = pd.DataFrame(results_list)
            # unique_symbols = results_df['symbol'].unique().tolist()

            # prices = {}
            # for symbol in unique_symbols:
            #     if symbol != 'cash':
            #         print(symbol)
            #         price = get_live_price_nse(symbol)
            #         prices[symbol] = price
            # print(results_df.shape)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(f"Fetched {len(results_list)} rows in {elapsed_time:.3f} seconds")
            # Print first 5 rows
            for r in results_list:
                portfolio_id = r.get('threshold_portfolio_id')
                print(portfolio_id)
                monitor_portfolio_alerts.delay(portfolio_id)
            time.sleep(10)
