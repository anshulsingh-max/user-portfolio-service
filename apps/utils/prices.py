import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from django.conf import settings
from django.core.cache import caches

from dateutil.parser import parse

from apps.portfolio.constants import SERVICE_NAME, Exchange, Asset
from wrappers.market_pricer import MarketPricer

logger = logging.getLogger(__name__)


def __build_security_key(security, exchange):
    """
        Internal function to build unique key from security and exchange
        :param security: Name of security
        :param exchange: Name of exchange
        :return: Unique key
    """
    return f"{security}-{exchange}live"


def get_live_price_nse(security, force=True):
    """
        Gets live price from cache
        :param force:
        :param security: Name of security
        :return: Price
    """
    logger.info(f"In get_live_price_nse {security =}, {force =}")
    price_dict = caches[settings.MARKET_PRICER_CACHE].get(__build_security_key(security, Exchange.NSE.value))
    logger.info(f"{price_dict =}")
    if not price_dict and force:
        logger.info("Price does not exist in cache.")
        market_pricer = MarketPricer(service_user=SERVICE_NAME)
        prices = market_pricer.get_live_prices(security,
                                               exchange=Exchange.NSE.value)
        logger.info(f"Price Fetched from API {prices =}")
        price = prices.get(security)
        price_dict = {
            "security": security,
            "exchange": Exchange.NSE.value,
            "price": price.get("price"),
            "timestamp": parse(price.get("timestamp"))
        }
    logger.info(f"Returning prices: {price_dict =}")
    return price_dict


def enrich_with_live_prices(portfolio_df: pd.DataFrame, max_threads: int = 10) -> pd.DataFrame:
    """
    Enriches the input portfolio DataFrame with live NSE prices for each unique symbol.

    This function:
      - Extracts unique symbols from the DataFrame
      - Fetches live prices in parallel using ThreadPoolExecutor
      - Maps fetched prices back into the DataFrame as `live_price`

    Args:
        portfolio_df (pd.DataFrame): Input DataFrame containing a `symbol` column.
        max_threads (int): Maximum number of threads for parallel execution.

    Returns:
        pd.DataFrame: DataFrame with an additional `live_price` column.
    """
    if "symbol" not in portfolio_df.columns:
        raise ValueError("Input DataFrame must contain a 'symbol' column.")

    symbols_list = portfolio_df["symbol"].dropna().unique().tolist()
    logger.info(f"[LivePriceService] Starting live price enrichment for {len(symbols_list)} symbols.")

    symbol_to_price_map: dict[str, float | None] = {}

    logger.info(f"[LivePriceService] Launching parallel fetch with {max_threads} threads.")
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_symbol_map = {
            executor.submit(get_live_price_nse, symbol): symbol for symbol in symbols_list if symbol != Asset.CASH.value
        }

        for future in as_completed(future_to_symbol_map):
            current_symbol = future_to_symbol_map[future]
            try:
                price_response = future.result()
                live_price = price_response.get("price") if price_response else None
                symbol_to_price_map[current_symbol] = live_price

                if live_price is not None:
                    logger.info(f"[LivePriceService] {current_symbol}: {live_price}")
                else:
                    logger.warning(f"[LivePriceService] No live price found for {current_symbol}")

            except Exception as error:
                logger.exception(f"[LivePriceService] Error fetching price for {current_symbol}: {error}")
                symbol_to_price_map[current_symbol] = None

    logger.info("[LivePriceService] Mapping live prices back to portfolio DataFrame.")
    portfolio_df["live_price"] = portfolio_df["symbol"].map(symbol_to_price_map)

    symbols_without_prices = [
        symbol for symbol, price in symbol_to_price_map.items() if price is None
    ]
    if symbols_without_prices:
        logger.info(f"[LivePriceService] Live prices unavailable for: {symbols_without_prices}")

    logger.info(
        f"[LivePriceService] Successfully enriched DataFrame with live prices for {len(symbol_to_price_map)} symbols.")
    logger.info(f"Records: {portfolio_df.shape =}")
    return portfolio_df


def compute_invested_and_current_values(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute invested and current values for each holding in the portfolio.

    invested_value = quantity * avg_buy_price
    current_value = quantity * live_price
    """
    logger.info("Computing invested and current values for each holding...")

    portfolio_df["invested_value"] = portfolio_df["quantity"] * portfolio_df["avg_buy_price"]
    portfolio_df["current_value"] = portfolio_df["quantity"] * portfolio_df["live_price"]

    logger.info("Sample after computing values:\n%s", portfolio_df.head())
    logger.info(f"Records: {portfolio_df.shape =}")
    return portfolio_df


def aggregate_basket_level_summary(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate basket-level totals and target percentage.
    Groups by threshold_portfolio_id and computes total invested/current value and basket target %.
    """
    logger.info("Aggregating basket-level totals and target percentages...")

    basket_summary = (
        portfolio_df.groupby("threshold_portfolio_id", as_index=False)
        .agg(
            basket_total_invested_value=pd.NamedAgg(column="invested_value", aggfunc="sum"),
            basket_total_current_value=pd.NamedAgg(column="current_value", aggfunc="sum"),
            basket_target_pct=pd.NamedAgg(column="target_pct", aggfunc="first"),
        )
    )

    logger.info("Basket summary preview:\n%s", basket_summary.head())
    logger.info(f"Records: {basket_summary.shape =}")
    return basket_summary


def compute_basket_performance(basket_summary: pd.DataFrame) -> pd.DataFrame:
    """
    Compute basket performance as a percentage and determine if PT (Profit Target) is achieved.
    """
    logger.info("Computing basket performance and evaluating profit targets...")

    basket_summary["pt_achieved_pct"] = (
                                                (basket_summary["basket_total_current_value"] - basket_summary[
                                                    "basket_total_invested_value"])
                                                / basket_summary["basket_total_invested_value"]
                                        ) * 100

    basket_summary["basket_pt_met"] = (
            basket_summary["pt_achieved_pct"] >= basket_summary["basket_target_pct"]
    )

    logger.info("Basket performance summary:\n%s", basket_summary.head())
    logger.info(f"Records: {basket_summary.shape =}")
    return basket_summary


def merge_basket_results_with_portfolio(
        portfolio_df: pd.DataFrame, basket_summary: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge basket-level results back to the original portfolio dataframe.
    """
    logger.info("Merging basket-level results back to the portfolio dataframe...")
    merged_df = pd.merge(portfolio_df, basket_summary, on="threshold_portfolio_id", how="left")
    logger.info("Merged portfolio preview:\n%s", merged_df.head())
    logger.info(f"Records: {merged_df.shape =}")
    return merged_df


def evaluate_basket_profit_targets(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluate whether each basket (threshold_portfolio_id) has met its profit target (PT).
    Basket PT is met if total % gain >= basket target %.
    """
    logger.info("Starting basket-level profit target evaluation...")

    if portfolio_df.empty:
        logger.info("Input dataframe is empty. Skipping evaluation.")
        return portfolio_df

    portfolio_df = compute_invested_and_current_values(portfolio_df)
    basket_summary = aggregate_basket_level_summary(portfolio_df)
    basket_summary = compute_basket_performance(basket_summary)
    logger.info("Basket-level profit target evaluation completed successfully.")
    logger.info(f"Records: {basket_summary.shape =}")
    return basket_summary


def get_live_prices(security, force=True):
    """
        Gets live price from cache
        :param force:
        :param security: Name of security
        :return: Price
    """
    logger.info(f"In get_live_prices {security =}, {force =}")
    try:
        price_dict = caches[settings.MARKET_PRICER_CACHE].get(__build_security_key(security, Exchange.NSE.value))
        logger.info(f"{price_dict =}")
        if not price_dict and force:
            logger.info("Price does not exist in cache.")
            market_pricer = MarketPricer(service_user=SERVICE_NAME)
            prices = market_pricer.get_live_prices(security,
                                                   exchange=Exchange.NSE.value)
            logger.info(f"Price Fetched from API {prices =}")
            price = prices.get(security)
            price_dict = {
                "security": security,
                "exchange": Exchange.NSE.value,
                "price": price.get("price"),
                "timestamp": parse(price.get("timestamp"))
            }
        logger.info(f"Returning prices: {price_dict =}")
        return price_dict
    except Exception as e:
        logger.info(f"Error fetching price for {security}: {e}")
        logger.exception(e)
        return {
                "security": security,
                "exchange": Exchange.NSE.value,
                "price": None,
                "timestamp": None
            }
