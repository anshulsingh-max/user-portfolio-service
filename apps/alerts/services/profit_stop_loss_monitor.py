"""apps/alerts/services/profit_stop_loss_monitoring.py

End-to-end monitoring for portfolio-level and holding-level threshold rules.

The `AlertMonitoring` class is conceptually similar to
`apps/portfolio/services/profit_stop_loss_monitor.py::ProfitStopLossMonitor` but
operates on the generic `UserPortfolioThreshold` and `HoldingThreshold` rule
models. It walks through all *active* portfolios/holdings, evaluates their
thresholds using live market prices, and sends notifications when rules are
triggered.

Only minimal business logic is included here – extend the *_evaluate_* helper
methods as the product requirements evolve (e.g. trailing-SL, time-based cool-
off, etc.).
"""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from bw_essentials.services.master_data import MasterData
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q

from apps.portfolio.constants import NotificationEventsMTF, ProductTypes, Asset, BrokerEnum
from apps.utils.prices import get_live_price_nse
from apps.portfolio.services.user_instruction import (
    user_portfolio_business_event_callback,
)
from apps.portfolio.models import UserPortfolio
from apps.holdings.models import Holding
from apps.alerts.models.user_portfolio_threshold import UserPortfolioThreshold
from apps.alerts.models.holding_threshold import HoldingThreshold
from apps.alerts.services.stop_loss_alert import get_stop_loss_alerts
from apps.alerts.constants import (
    PortfolioThresholdTypes,
    Status,
    PortfolioSides,
    ACTIVE_PORTFOLIOS_CACHE_KEY,
    ACTIVE_PORTFOLIOS_CACHE_TIMEOUT,
    ACTIVE_HOLDINGS_THRESHOLD_CACHE_KEY,
    HOLDINGS_CACHE_KEY,
    HOLDINGS_CACHE_TIMEOUT,
    PORTFOLIO_THRESHOLDS_CACHE_PREFIX,
    PORTFOLIO_THRESHOLDS_CACHE_TIMEOUT,
)
from middlewares.constants import SERVICE, DOMAIN

logger = logging.getLogger(__name__)


class AlertMonitoring:
    """Monitors *active* `UserPortfolio` and `Holding` thresholds.

    Usage:
        monitor = AlertMonitoring()
        monitor.run_monitor()
    """
    def __init__(self) -> None:
        logger.info("AlertMonitoring.__init__ - start")
        logger.info("Initializing AlertMonitoring service")
        self.notification_gap = timedelta(hours=settings.MONITORING_NOTIFICATION_DELAY)
        logger.info("AlertMonitoring.__init__ - end")

    @staticmethod
    def get_active_user_portfolios():
        logger.info("get_active_user_portfolios - start")
        """Return *active* `UserPortfolio` queryset using cache first."""
        logger.info("Fetching active user portfolios from cache")
        portfolios = cache.get(ACTIVE_PORTFOLIOS_CACHE_KEY)
        if portfolios is None:
            logger.info("Cache miss for active user portfolios")
            portfolios = list(
                UserPortfolio.objects.filter(status=Status.ACTIVE,
                                             product_type=ProductTypes.MTF.value).values_list("id",
                                                                                              flat=True)
            )
            cache.set(ACTIVE_PORTFOLIOS_CACHE_KEY, portfolios, timeout=ACTIVE_PORTFOLIOS_CACHE_TIMEOUT)
            logger.info("Active user portfolios cached")
        logger.info("Active user portfolios fetched from cache")
        logger.info("get_active_user_portfolios - end")
        return portfolios

    @staticmethod
    def get_active_holdings_thresholds():
        logger.info("get_active__holdings_thresholds - start")
        """Return *active* `HoldingThreshold` queryset using cache first."""
        logger.info("Fetching active holdings thresholds from cache")
        thresholds = cache.get(ACTIVE_HOLDINGS_THRESHOLD_CACHE_KEY)
        if thresholds is None:
            logger.info("Cache miss for active holdings thresholds")
            thresholds = list(
                HoldingThreshold.objects.filter(status=Status.ACTIVE).values_list("id", flat=True)
            )
            cache.set(ACTIVE_HOLDINGS_THRESHOLD_CACHE_KEY, thresholds, timeout=ACTIVE_PORTFOLIOS_CACHE_TIMEOUT)
            logger.info("Active holdings thresholds cached")
        logger.info("Active holdings thresholds fetched from cache")
        logger.info("get_active__holdings_thresholds - end")
        return thresholds

    @staticmethod
    def get_all_holdings():
        logger.info("get_all_holdings - start")
        """Return a mapping of all holdings keyed by *id* using cache first."""
        logger.info("Fetching holdings map from cache")
        holdings_map = cache.get(HOLDINGS_CACHE_KEY)
        if holdings_map is None:
            logger.info("Cache miss for holdings map")
            holdings_map = {
                str(h.id): h
                for h in Holding.objects.filter(user_portfolio__product_type=ProductTypes.MTF.value
                                                ).only("id", "symbol", "avg_buy_price").exclude(
                    symbol=Asset.CASH.value).filter(quantity__gt=0)
            }
            cache.set(HOLDINGS_CACHE_KEY, holdings_map, timeout=HOLDINGS_CACHE_TIMEOUT)
            logger.info("Holdings map cached – %s entries", len(holdings_map))
        logger.info("get_all_holdings - end")
        return holdings_map

    @staticmethod
    def get_portfolio_thresholds(portfolio_id: int):
        """Return *active* `UserPortfolioThreshold` IDs for a portfolio using cache first."""
        logger.info("get_portfolio_thresholds - start | portfolio_id=%s", portfolio_id)
        cache_key = f"{PORTFOLIO_THRESHOLDS_CACHE_PREFIX}{portfolio_id}"
        logger.info("Fetching portfolio thresholds from cache | key=%s", cache_key)
        threshold_ids = cache.get(cache_key)
        if threshold_ids is None:
            logger.info("Cache miss for portfolio thresholds | portfolio_id=%s", portfolio_id)
            threshold_ids = list(
                UserPortfolioThreshold.objects.filter(
                    portfolio_id=str(portfolio_id), status=Status.ACTIVE
                ).values_list("id", flat=True)
            )
            cache.set(cache_key, threshold_ids, timeout=PORTFOLIO_THRESHOLDS_CACHE_TIMEOUT)
            logger.info("Portfolio thresholds cached | portfolio_id=%s count=%s", portfolio_id, len(threshold_ids))
        logger.info("get_portfolio_thresholds - end | portfolio_id=%s", portfolio_id)
        return threshold_ids

    def get_active_symbols_with_thresholds(self):
        logger.info("get_active_symbols_with_thresholds - start")

        now = timezone.now()
        thresholds = HoldingThreshold.objects.filter(
            status=Status.ACTIVE
        ).filter(
            Q(last_notification_sent_at__isnull=True) |
            Q(last_notification_sent_at__lte=now - self.notification_gap)
        )

        if not thresholds.exists():
            logger.info("No active holding thresholds found")
            return []

        holding_ids = [t.holding_id for t in thresholds]
        holdings = Holding.objects.filter(
            id__in=holding_ids,
            quantity__gt=0,
            user_portfolio__product_type=ProductTypes.MTF.value
        ).select_related('user_portfolio')

        holdings_map = {str(h.id): h for h in holdings}

        records = []
        for threshold in thresholds:
            holding = holdings_map.get(str(threshold.holding_id))
            if not holding:
                continue
            up = holding.user_portfolio
            if holding.quantity > 0:
                records.append({
                    "symbol": holding.symbol,
                    "holding_id": holding.id,
                    "user_id": up.user_id,
                    "portfolio_id": up.portfolio_id,
                    "user_portfolio_id": up.id,
                    "target_value": threshold.target_value,
                    "avg_buy_price": holding.avg_buy_price,
                    "target_pct": threshold.target_pct,
                    "stop_loss_price": holding.avg_buy_price - (holding.avg_buy_price * threshold.target_pct / 100)
                })

        logger.info("get_active_symbols_with_thresholds - end | count=%s", len(records))
        return records

    def run_monitor(self) -> None:
        logger.info("run_monitor - start")
        """Entry-point – iterate through portfolios & holdings and evaluate."""
        self._monitor_user_portfolios()
        self._monitor_holdings()
        logger.info("run_monitor - end")

    def _monitor_user_portfolios(self) -> None:
        logger.info("_monitor_user_portfolios - start")
        """Scan all active user portfolios and evaluate thresholds."""
        portfolios = self.get_active_user_portfolios()
        logger.info("Scanning %s active user portfolios for thresholds", len(portfolios))

        for portfolio in portfolios:
            self.monitor_single_user_portfolio(portfolio)
        logger.info("_monitor_user_portfolios - end")

    def monitor_single_user_portfolio(self, portfolio_id: int) -> None:
        logger.info("monitor_single_user_portfolio - start | portfolio_id=%s", portfolio_id)
        """Scan a single user portfolio and evaluate thresholds."""
        logger.info("Scanning user portfolio %s for thresholds", portfolio_id)
        threshold_ids = self.get_portfolio_thresholds(portfolio_id)

        if not threshold_ids:
            logger.info("No active thresholds found for portfolio %s", portfolio_id)
            return

        logger.info("%s thresholds found for portfolio %s", len(threshold_ids), portfolio_id)

        thresholds = UserPortfolioThreshold.objects.filter(id__in=threshold_ids)

        portfolio = UserPortfolio.objects.get(id=portfolio_id)
        for threshold in thresholds:
            self._evaluate_portfolio_threshold(portfolio, threshold)
        logger.info("monitor_single_user_portfolio - end | portfolio_id=%s", portfolio_id)

    def _evaluate_portfolio_threshold(
        self, portfolio: UserPortfolio, threshold: UserPortfolioThreshold
    ) -> None:
        logger.info("_evaluate_portfolio_threshold - start | portfolio_id=%s, threshold_id=%s", portfolio.id, threshold.id)
        """Evaluate a single `UserPortfolioThreshold` against live prices."""
        holdings_map = self.get_all_holdings()
        portfolio_holdings = [
            (h.symbol, h.quantity, h.avg_buy_price)
            for h in holdings_map.values()
            if h.user_portfolio_id == portfolio.id and h.quantity > 0 and h.symbol != Asset.CASH.value
        ]
        invested_amount: Decimal = Decimal("0")
        current_value: Decimal = Decimal("0")
        for symbol, qty, buy_price in portfolio_holdings:
            logger.info(f"Processing portfolio threshold {portfolio.id =}, {symbol =}, {qty =}, {buy_price =}")
            invested_amount += Decimal(qty) * Decimal(buy_price)
            price_dict = get_live_price_nse(symbol)
            price = Decimal(str(price_dict.get("price", 0)))
            current_value += Decimal(qty) * price
        if invested_amount == 0:
            logger.info("Portfolio %s has no invested amount; skipping", portfolio.id)
            return

        pct_change = (current_value - invested_amount) / invested_amount * Decimal("100")
        logger.info(
            "Portfolio %s – invested=%s current=%s pct_change=%s%%",
            portfolio.id,
            invested_amount,
            current_value,
            pct_change,
        )

        if threshold.threshold_type == PortfolioThresholdTypes.PROFIT_TARGET:
            triggered = self._is_profit_target_hit(
                pct_change, current_value, threshold
            )
            event_name = NotificationEventsMTF.PROFIT_TARGET_HIT_1_MTF.value
        else:
            triggered = self._is_stop_loss_hit(pct_change, current_value, threshold)
            event_name = NotificationEventsMTF.STOP_LOSS_HIT_MTF.value

        if triggered:
            logger.info("Portfolio %s triggered %s", portfolio.id, event_name)
            self._handle_trigger(threshold, portfolio, event_name)
        logger.info("_evaluate_portfolio_threshold - end | portfolio_id=%s, threshold_id=%s", portfolio.id, threshold.id)

    def _monitor_holdings(self) -> None:
        logger.info("_monitor_holdings - start")
        thresholds = self.get_active_holdings_thresholds()
        logger.info("Scanning %s active holding thresholds", len(thresholds))
        for threshold in thresholds:
            self._evaluate_holding_threshold(threshold)
        logger.info("_monitor_holdings - end")

    def _evaluate_holding_threshold(self, threshold_id: int) -> None:
        logger.info("_evaluate_holding_threshold - start | threshold_id=%s", threshold_id)
        """Evaluate a single `HoldingThreshold` identified by its *id*."""

        try:
            threshold = HoldingThreshold.objects.get(id=threshold_id)
        except HoldingThreshold.DoesNotExist:
            logger.info("HoldingThreshold %s does not exist", threshold_id)
            return

        holdings_map = self.get_all_holdings()
        symbol_holding = holdings_map.get(str(threshold.holding_id))

        if not symbol_holding:
            logger.info("No holding found for threshold %s (holding_id=%s)", threshold_id, threshold.holding_id)
            return

        price_dict = get_live_price_nse(symbol_holding.symbol)
        current_price = Decimal(str(price_dict.get("price", 0)))
        buy_price = Decimal(str(symbol_holding.avg_buy_price))
        pct_change = (current_price - buy_price) / buy_price * Decimal("100")
        logger.info(
            "Holding %s(%s) – buy=%s current=%s pct_change=%s%%",
            symbol_holding.symbol,
            symbol_holding.id,
            buy_price,
            current_price,
            pct_change,
        )

        if threshold.threshold_type == PortfolioThresholdTypes.PROFIT_TARGET.value:
            triggered = self._is_profit_target_hit(
                pct_change, current_price, threshold
            )
            event_name = NotificationEventsMTF.HOLDING_PROFIT_TARGET_HIT.value
        else:
            triggered = self._is_stop_loss_hit(pct_change, current_price, threshold)
            event_name = NotificationEventsMTF.STOP_LOSS_HIT_MTF.value

        if triggered:
            self._handle_trigger(threshold, symbol_holding.user_portfolio, event_name)
        logger.info("_evaluate_holding_threshold - end | threshold_id=%s", threshold_id)

    def monitor_single_holding_threshold(self, threshold_id: int) -> None:
        logger.info("monitor_single_holding_threshold - start | threshold_id=%s", threshold_id)
        """Scan a single holding threshold and evaluate it."""
        self._evaluate_holding_threshold(threshold_id)
        logger.info("monitor_single_holding_threshold - end | threshold_id=%s", threshold_id)

    @staticmethod
    def _is_profit_target_hit(pct_change: Decimal, value: Decimal, threshold) -> bool:
        logger.info("_is_profit_target_hit - start | threshold_id=%s", getattr(threshold, 'id', 'N/A'))
        """Return True if *profit target* conditions met, incorporating position side."""
        side_mult = 1 if threshold.side == PortfolioSides.LONG else -1
        logger.info(f"Checking profit target | side={threshold.side}, pct_change={pct_change}, "
                    f"value={value}, target_pct={threshold.target_pct}, target_value={threshold.target_value}")

        cond_pct = threshold.target_pct and (pct_change * side_mult) >= threshold.target_pct
        cond_val = threshold.target_value and (value * side_mult) >= threshold.target_value

        hit = bool(cond_pct or cond_val)
        logger.info(f"Profit target condition -> cond_pct={cond_pct}, cond_val={cond_val}, hit={hit}")
        logger.info("_is_profit_target_hit - end | threshold_id=%s, hit=%s", getattr(threshold, 'id', 'N/A'), hit)
        return hit

    @staticmethod
    def _is_stop_loss_hit(pct_change: Decimal, value: Decimal, threshold) -> bool:
        logger.info("_is_stop_loss_hit - start | threshold_id=%s", getattr(threshold, 'id', 'N/A'))
        """Return True if *stop loss* conditions met, incorporating position side."""
        side_mult = 1 if threshold.side == PortfolioSides.LONG else -1
        logger.info(f"Checking stop loss | side={threshold.side}, pct_change={pct_change}, "
                    f"value={value}, target_pct={threshold.target_pct}, target_value={threshold.target_value}")

        cond_pct = threshold.target_pct and (pct_change * side_mult) <= -threshold.target_pct
        cond_val = threshold.target_value and (value * side_mult) <= threshold.target_value

        hit = bool(cond_pct or cond_val)
        logger.info(f"Stop loss condition -> cond_pct={cond_pct}, cond_val={cond_val}, hit={hit}")
        logger.info("_is_stop_loss_hit - end | threshold_id=%s, hit=%s", getattr(threshold, 'id', 'N/A'), hit)
        return hit

    def _handle_trigger(self, threshold, basket: UserPortfolio, event_name: str) -> None:
        logger.info("_handle_trigger - start | threshold_id=%s", threshold.id)
        """Send notification and persist trigger timestamps respecting gap."""
        if not MasterData(service_user=SERVICE).is_market_open(broker=BrokerEnum.HDFC.value,
                                                               domain=DOMAIN):
            logger.info("Market is closed. Skipping scheduler portfolio monitoring task.")
            return
        now = timezone.now()
        if threshold.last_notification_sent_at and (
            now - threshold.last_notification_sent_at
        ) < self.notification_gap:
            logger.info("Notification gap not met for threshold %s", threshold.id)
            return

        with transaction.atomic():
            threshold.triggered_at = now
            threshold.save(update_fields=["triggered_at"])

        payload = {
            "event_name": event_name,
            "username": basket.user_id,
            "platform": ProductTypes.MTF.value,
            "basket_id": basket.id,
            "model_id": basket.portfolio_id,
        }

        logger.info("Sending notification for threshold %s", threshold.id)
        response, status = user_portfolio_business_event_callback(payload)
        logger.info(f"response: {response}, status: {status}")
        threshold.reason = f"response: {response}, status: {status}"
        threshold.save(update_fields=["reason"])
        if status:
            threshold.last_notification_sent_at = now
            threshold.save(update_fields=["last_notification_sent_at"])
            logger.info("Updated last_notification_sent_at for threshold %s", threshold.id)
        else:
            logger.info("Notification not sent successfully for threshold %s; will retry later", threshold.id)
        logger.info("_handle_trigger - end | threshold_id=%s", threshold.id)

    def handle_trigger(self, threshold, user_id, user_portfolio_id, portfolio_id, event_name: str) -> None:
        logger.info("_handle_trigger - start | threshold_id=%s", threshold.id)
        """Send notification and persist trigger timestamps respecting gap."""
        if not MasterData(service_user=SERVICE).is_market_open(broker=BrokerEnum.HDFC.value,
                                                               domain=DOMAIN):
            logger.info("Market is closed. Skipping scheduler holding monitoring task.")
            return
        now = timezone.now()
        if threshold.last_notification_sent_at and (
            now - threshold.last_notification_sent_at
        ) < self.notification_gap:
            logger.info("Notification gap not met for threshold %s", threshold.id)
            return

        with transaction.atomic():
            threshold.triggered_at = now
            threshold.save(update_fields=["triggered_at"])
        
        # fetching stop loss hit constituents 
        stop_loss_hit_constituents = get_stop_loss_alerts(user_portfolio_id)
        logger.info("stop_loss_hit_constituents: %s", stop_loss_hit_constituents)

        payload = {
            "event_name": event_name,
            "username": user_id,
            "platform": ProductTypes.MTF.value,
            "basket_id": user_portfolio_id,
            "model_id": portfolio_id,
            "stop_loss_list": stop_loss_hit_constituents
        }
        logger.info("payload: %s", payload)
        logger.info("Sending notification for threshold %s", threshold.id)
        response, status = user_portfolio_business_event_callback(payload)
        logger.info(f"response: {response}, status: {status}")
        threshold.reason = f"response: {response}, status: {status}"
        threshold.save(update_fields=["reason"])
        if status:
            threshold.last_notification_sent_at = now
            threshold.save(update_fields=["last_notification_sent_at"])
            logger.info("Updated last_notification_sent_at for threshold %s", threshold.id)
        else:
            threshold.status = Status.ACTIVE
            threshold.save(update_fields=["status"])
            logger.info("Notification not sent successfully for threshold %s; will retry later", threshold.id)
        logger.info("_handle_trigger - end | threshold_id=%s", threshold.id)
