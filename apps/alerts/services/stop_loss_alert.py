import logging
from typing import List, Dict

from apps.holdings.models import Holding
from apps.alerts.models import HoldingThreshold
from apps.alerts.constants import PortfolioThresholdTypes, Status, Asset
from apps.utils.prices import get_live_prices

logger = logging.getLogger(__name__)


def get_stop_loss_alerts(user_portfolio_id: int) -> List[Dict]:
    """
    Fetch holdings with active stop loss thresholds and check if they have hit stop loss.

    Logic:
    1. Fetch holdings for the user portfolio where quantity > 0
    2. For each holding, get active stop loss thresholds
    3. Fetch live prices for each symbol
    4. Compare: stop_loss_price >= live_price to determine if stop loss is hit
    5. Return list of holdings that have hit their stop loss

    Args:
        user_portfolio_id (int): The user portfolio ID to check

    Returns:
        List[Dict]: List of holdings that hit stop loss with format:
            {
                "symbol": str,
                "target_pct": float,
                "avg_buy_price": float,
                "stop_loss_price": float,
                "live_price": float
            }

    Raises:
        Exception: If live price fetch fails (price is None)
    """
    logger.info("Getting stop loss alerts for user_portfolio_id=%s", user_portfolio_id)

    # Fetch holdings with quantity > 0
    holdings = Holding.objects.filter(
        user_portfolio_id=user_portfolio_id,
        quantity__gt=0,
    ).exclude(symbol=Asset.CASH.value)

    if not holdings.exists():
        logger.info("No holdings found for user_portfolio_id=%s", user_portfolio_id)
        return []

    logger.info("Found %d holdings for user_portfolio_id=%s", holdings.count(), user_portfolio_id)

    # Build a map of holding_id to holding object
    holdings_map = {str(holding.id): holding for holding in holdings}
    holding_ids = list(holdings_map.keys())

    # Fetch processing stop loss thresholds for these holdings.
    # In the alert task flow, threshold status is set to PROCESSING
    # before handle_trigger invokes this function.
    thresholds = HoldingThreshold.objects.filter(
        holding_id__in=holding_ids,
        threshold_type=PortfolioThresholdTypes.STOP_LOSS,
        status=Status.PROCESSING
    )

    if not thresholds.exists():
        logger.info("No processing stop loss thresholds found for holdings in user_portfolio_id=%s", user_portfolio_id)
        return []

    logger.info("Found %d processing stop loss thresholds", thresholds.count())

    stop_loss_alerts = []

    for threshold in thresholds:
        holding = holdings_map.get(str(threshold.holding_id))
        if not holding:
            logger.warning("Holding not found for threshold holding_id=%s", threshold.holding_id)
            continue

        # Calculate stop loss price: avg_buy_price - (avg_buy_price * target_pct / 100)
        # check for target_pct is not None
        stop_loss_price = holding.avg_buy_price - (holding.avg_buy_price * threshold.target_pct / 100)

        logger.info("Fetching live price for symbol=%s", holding.symbol)

        # Fetch live price
        price_dict = get_live_prices(holding.symbol)
        live_price = price_dict.get('price')

        # If live price fetch fails, log exception and raise error
        if live_price is None:
            logger.exception("Failed to fetch live price for symbol=%s", holding.symbol)
            raise Exception(f"Unable to fetch live price for symbol {holding.symbol}")

        logger.info("Live price for %s: %s, Stop loss price: %s",
                   holding.symbol, live_price, stop_loss_price)

        # Check if stop loss is hit: stop_loss_price >= live_price
        if stop_loss_price >= live_price:
            logger.info("Stop loss hit for symbol=%s (stop_loss_price=%s >= live_price=%s)",
                       holding.symbol, stop_loss_price, live_price)

            stop_loss_alerts.append({
                "symbol": holding.symbol,
                "target_pct": threshold.target_pct,
                "avg_buy_price": holding.avg_buy_price,
                "stop_loss_price": stop_loss_price,
                "live_price": live_price
            })

    logger.info("Found %d holdings with stop loss hit", len(stop_loss_alerts))
    return stop_loss_alerts
