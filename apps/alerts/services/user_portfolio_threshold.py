import logging
import time
from datetime import timedelta
from typing import Any

import pandas as pd
from django.conf import settings
from django.db import transaction, router
from django.db.models import OuterRef, Exists, CharField, IntegerField, Subquery, FloatField, Q
from django.db.models.functions import Cast
from django.utils import timezone

from apps.alerts.constants import Status, PortfolioSides, PortfolioThresholdTypes,Asset
from apps.alerts.models import UserPortfolioThreshold
from apps.alerts.serializers.user_portfolio_threshold import UserPortfolioThresholdSerializer
from apps.holdings.models import Holding
from apps.portfolio.constants import Asset, ProductTypes, CashTransaction, RebalanceTypes
from apps.utils.cache_lock import acquire_lock, release_lock
from apps.utils.prices import get_live_price_nse, evaluate_basket_profit_targets, enrich_with_live_prices

logger = logging.getLogger(__name__)


def create_user_portfolio_threshold(validated_data: dict) -> str | Any:
    """
    Create a UserPortfolioThreshold for a portfolio-like entity.

    This function creates a new threshold (Profit Target, Stop Loss, etc.) for a given
    portfolio without automatically deactivating existing thresholds. This allows
    multiple thresholds of the same type (e.g., multiple PTs) to coexist for the same
    portfolio and side.

    Args:
        validated_data (dict): Dictionary containing threshold data. Required keys:
            - portfolio_type (str): Type of portfolio entity (e.g., USER_PORTFOLIO, BASKET)
            - portfolio_id (str): Identifier of the portfolio entity
            - side (str): Position side (long/short)
            - threshold_type (str): Type of threshold (PT/SL)
            - status (str): Status of the threshold (e.g., ACTIVE)
            - target_pct (Decimal, optional): Percentage-based threshold
            - target_value (Decimal, optional): Absolute value threshold
            - source (str, optional): Origin of the threshold (User/Admin/Dealer)

    Returns:
        UserPortfolioThreshold: The newly created threshold instance.

    Notes:
        - Multiple thresholds of the same type (e.g., multiple PTs) can coexist for a
          single portfolio and side.
        - No automatic deactivation is performed; management of active/inactive thresholds
          should be handled separately if needed.
        - Uses a serializer for validation and creation, raising exceptions for invalid data.
    """
    portfolio_id = validated_data.get('portfolio_id')
    portfolio_type = validated_data.get('portfolio_type')
    side = validated_data.get('side')
    threshold_type = validated_data.get('threshold_type')

    lock_key = f"threshold_lock:{portfolio_type}:{portfolio_id}:{side}:{threshold_type}"

    logger.info(f"Trying to acquire lock for {lock_key}")
    got_lock = acquire_lock(lock_key)
    if not got_lock:
        logger.info(f"Another threshold creation is already in progress for {lock_key}")
        return "Another threshold creation is already in progress. Please retry shortly."

    db_alias = router.db_for_write(UserPortfolioThreshold)

    try:
        with transaction.atomic(using=db_alias):
            logger.info(f"Creating UserPortfolioThreshold for {portfolio_id=} {threshold_type=} {side=}")
            filters = {
                "portfolio_id": portfolio_id,
                "portfolio_type": portfolio_type,
                "side": side,
                "threshold_type": threshold_type,
                "status": Status.ACTIVE,
            }
            updated = UserPortfolioThreshold.objects.filter(**filters).update(status=Status.INACTIVE)
            logger.info(f"Deactivated {updated} existing active thresholds for {portfolio_id=}")
            serializer = UserPortfolioThresholdSerializer(data=validated_data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()

            logger.info(f"Created new threshold {instance.id} for portfolio {portfolio_id}")

            return instance
    except Exception as exc:
        logger.info(f"[ERROR] Failed to create UserPortfolioThreshold for {portfolio_id}: {exc}")
        logger.exception(exc)
        raise

    finally:
        release_lock(lock_key)
        logger.info(f"[LOCK] Released lock for {lock_key}")


def update_user_portfolio_threshold(threshold_id: int, update_data: dict) -> UserPortfolioThreshold:
    """
    Update a UserPortfolioThreshold with provided fields.
    - Only applies non-null values.
    - Business logic handled in signals.
    """
    try:
        logger.info(f"Updating UserPortfolioThreshold {threshold_id =}, {update_data =}")
        db_alias = router.db_for_write(UserPortfolioThreshold)
        with transaction.atomic(using=db_alias):
            threshold = (
                UserPortfolioThreshold.objects.using(db_alias)
                .select_for_update()
                .get(id=threshold_id)
            )

            for key, value in update_data.items():
                logger.info(f"Updating {key =}, {value =}")
                if value is not None:
                    setattr(threshold, key, value)

            threshold.save()
            threshold.refresh_from_db()
            logger.info(f"Updated UserPortfolioThreshold {threshold_id =}")
            return threshold
    except UserPortfolioThreshold.DoesNotExist as exc:
        logger.info(f"Threshold with ID {threshold_id} does not exist.")
        logger.exception(exc)
        raise
    except Exception as exc:
        logger.info("Error updating UserPortfolioThreshold")
        logger.exception(exc)
        raise


def fetch_portfolio_holdings_by_thresholds(status: str, portfolio_type: str):
    thresholds = UserPortfolioThreshold.objects.filter(
        status=status,
        portfolio_type=portfolio_type,
        portfolio_id=Cast(OuterRef("user_portfolio_id"), output_field=CharField()),
    )

    holdings = (
        Holding.objects.annotate(has_threshold=Exists(thresholds))
        .filter(has_threshold=True, quantity__gt=0)
        .exclude(symbol=Asset.CASH.value)
        .values("user_portfolio", "symbol", "quantity", "avg_buy_price")
        .distinct()
    )
    return list(holdings)


def get_active_thresholds(hours_ago: int = settings.MONITORING_NOTIFICATION_DELAY) -> pd.DataFrame:
    """
    Fetch all active user portfolio thresholds where the last notification
    was sent more than `hours_ago` hours ago.

    This function is efficient and only runs one SQL query.

    Args:
        hours_ago (int): Minimum hours elapsed since last notification.

    Returns:
        pd.DataFrame: DataFrame containing threshold_id, portfolio_id_int, target_pct
    """
    start_time = time.time()
    logger.info(f"[Step 1] Fetching active thresholds older than {hours_ago}h...")

    cutoff_time = timezone.now() - timedelta(hours=hours_ago)

    thresholds_qs = (
        UserPortfolioThreshold.objects
        .filter(status="active")
        .filter(
            Q(last_notification_sent_at__lte=cutoff_time) |
            Q(last_notification_sent_at__isnull=True)
        )
        .exclude(
            target_pct=0
        )
        .annotate(
            portfolio_id_int=Cast("portfolio_id", IntegerField())
        )
        .values(
            "id",
            "portfolio_id_int",
            "target_pct",
            "portfolio_id",
        )
    )

    thresholds_df = pd.DataFrame(list(thresholds_qs))

    logger.info(
        f"[Step 1] Retrieved {len(thresholds_df)} active thresholds in "
        f"{time.time() - start_time:.2f}s"
    )
    return thresholds_df


def get_holdings_with_active_thresholds(thresholds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fetch holdings linked to active thresholds (in bulk) and join using pandas.

    This approach:
      - Runs only one query for all holdings (no subqueries)
      - Joins data in-memory using pandas (fast for <= 1M rows)
      - Avoids correlated subquery overhead

    Args:
        thresholds_df (pd.DataFrame): Active thresholds DataFrame containing
            `portfolio_id_int`, `id` (threshold_id), and `target_pct`.

    Returns:
        pd.DataFrame: Holdings joined with threshold metadata.
    """
    start_time = time.time()
    logger.info("[Step 2] Fetching holdings for active threshold portfolios...")

    if thresholds_df.empty:
        logger.info("[Step 2] No active thresholds found. Returning empty DataFrame.")
        return pd.DataFrame()

    portfolio_ids = thresholds_df["portfolio_id_int"].unique().tolist()

    holdings_qs = (
        Holding.objects
        .filter(
            quantity__gt=0,
            user_portfolio_id__in=portfolio_ids,
            user_portfolio__product_type=ProductTypes.MTF.value
        )
        .exclude(symbol=Asset.CASH.value)
        .values("user_portfolio_id", "symbol", "quantity", "avg_buy_price")
    )

    holdings_df = pd.DataFrame(list(holdings_qs))

    if holdings_df.empty:
        logger.info("[Step 2] No holdings found for active thresholds.")
        return pd.DataFrame()

    merged_df = holdings_df.merge(
        thresholds_df,
        left_on="user_portfolio_id",
        right_on="portfolio_id_int",
        how="inner",
        suffixes=("", "_threshold")
    )

    merged_df.rename(
        columns={
            "id": "threshold_id",
            "portfolio_id": "threshold_portfolio_id"
        },
        inplace=True
    )

    logger.info(
        f"[Step 2] Joined {len(merged_df)} holdings with "
        f"{len(thresholds_df)} thresholds in {time.time() - start_time:.2f}s"
    )

    return merged_df[
        [
            "threshold_portfolio_id",
            "threshold_id",
            "symbol",
            "quantity",
            "avg_buy_price",
            "target_pct"
        ]
    ]


def fetch_unique_symbols_from_holdings(holdings_list):
    """
    Extract unique stock symbols from holdings list excluding cash.
    """
    logger.info("Fetching unique symbols from holdings")
    df = pd.DataFrame(holdings_list)
    if 'symbol' not in df.columns:
        return []
    return [symbol for symbol in df['symbol'].unique().tolist() if symbol.lower() != 'cash']


def fetch_live_prices_for_symbols(symbols: list):
    """
    Fetch live prices from NSE for a list of stock symbols.
    """
    logger.info("Fetching live prices for symbols")
    prices = {}
    for symbol in symbols:
        prices[symbol] = get_live_price_nse(symbol)
    return prices


def fetch_active_thresholds() -> pd.DataFrame:
    """
    Step 1: Fetch all active user-defined threshold portfolios.

    This function retrieves the currently active thresholds from the database
    or underlying service layer. These thresholds define profit targets that
    users have set for their investment baskets.

    Returns:
        pd.DataFrame: DataFrame or QuerySet of active thresholds.
    """
    start_time = time.time()
    logger.info("[Step 1] Fetching active thresholds...")
    thresholds_qs = get_active_thresholds()
    logger.info(f"[Step 1] Fetched active thresholds in {time.time() - start_time:.2f}s")
    return thresholds_qs


def fetch_holdings(thresholds_qs) -> pd.DataFrame:
    """
    Step 2: Fetch holdings linked to active thresholds.

    For each active threshold portfolio, this function retrieves the associated
    user holdings (symbol, quantity, buy price, etc.) that are subject to the
    defined profit targets.

    Args:
        thresholds_qs: QuerySet or list of active threshold portfolios.

    Returns:
        list: List of holdings dictionaries containing stock-level data.
    """
    start_time = time.time()
    logger.info("[Step 2] Fetching holdings with active thresholds...")
    holdings_list = get_holdings_with_active_thresholds(thresholds_qs)
    logger.info(f"[Step 2] Retrieved holdings in {time.time() - start_time:.2f}s")
    logger.info(f"[Step 2] Total holdings fetched: {len(holdings_list)}")
    return holdings_list


def enrich_dataframe_with_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 3: Enrich holdings DataFrame with live market prices.

    For each unique symbol in the DataFrame, this function fetches the
    latest live market price and attaches it as a new column `live_price`.

    Args:
        df (pd.DataFrame): DataFrame containing holdings with symbols.

    Returns:
        pd.DataFrame: Updated DataFrame with `live_price` column.
    """
    start_time = time.time()
    logger.info("[Step 3] Enriching DataFrame with live prices...")
    df_with_prices = enrich_with_live_prices(df)
    logger.info(f"[Step 3] Enriched DataFrame with live prices in {time.time() - start_time:.2f}s")
    logger.info(f"[Step 3] Live prices successfully attached for {df_with_prices['live_price'].notna().sum()} symbols")
    return df_with_prices


def evaluate_basket_targets(df_with_prices: pd.DataFrame) -> pd.DataFrame:
    """
    Step 4: Evaluate basket-level profit targets.

    This function aggregates stock-level data into basket-level summaries
    based on `threshold_portfolio_id`. It computes total invested value,
    total current value, and evaluates whether the profit target (PT)
    defined by the user has been met.

    Args:
        df_with_prices (pd.DataFrame): DataFrame enriched with live prices.

    Returns:
        pd.DataFrame: DataFrame with additional basket-level PT evaluation columns.
    """
    start_time = time.time()
    logger.info("[Step 4] Evaluating basket-level profit targets...")
    portfolio_with_pt = evaluate_basket_profit_targets(df_with_prices)
    logger.info(f"[Step 4] Evaluated basket-level PT in {time.time() - start_time:.2f}s")
    logger.info(f"[Step 4] Baskets evaluated: {portfolio_with_pt['threshold_portfolio_id'].nunique()}")
    return portfolio_with_pt


def filter_baskets_with_pt_hit(portfolio_with_pt: pd.DataFrame) -> pd.DataFrame:
    """
    Step 5: Filter baskets that have achieved or exceeded their profit targets.

    Args:
        portfolio_with_pt (pd.DataFrame): Portfolio DataFrame with PT evaluation.

    Returns:
        pd.DataFrame: Subset of DataFrame where `basket_pt_met` is True.
    """
    start_time = time.time()
    logger.info("[Step 5] Filtering baskets that have met profit targets...")
    basket_with_pt_hit = portfolio_with_pt[portfolio_with_pt["basket_pt_met"] == True]
    logger.info(f"[Step 5] Filtered baskets with PT hit in {time.time() - start_time:.2f}s")
    logger.info(f"[Step 5] Total baskets meeting PT: {basket_with_pt_hit['threshold_portfolio_id'].nunique()}")
    return basket_with_pt_hit


def run_basket_pt_evaluation() -> pd.DataFrame:
    """
    Executes the complete basket profit target evaluation pipeline.

    This pipeline performs the following steps sequentially:
        1. Fetch active threshold portfolios
        2. Retrieve associated holdings
        3. Enrich DataFrame with live prices
        4. Evaluate basket-level profit targets
        5. Filter baskets where PT has been met

    Returns:
        pd.DataFrame: Final DataFrame with basket-level PT evaluation.
    """
    start_time = time.time()
    logger.info("[Pipeline] Starting basket profit target evaluation pipeline...")

    thresholds_qs = fetch_active_thresholds()
    holdings_df = fetch_holdings(thresholds_qs)
    df_with_prices = enrich_dataframe_with_prices(holdings_df)
    portfolio_with_pt = evaluate_basket_targets(df_with_prices)
    baskets_with_pt_hit = filter_baskets_with_pt_hit(portfolio_with_pt)

    total_time = time.time() - start_time
    logger.info(f"[Pipeline] Completed basket PT evaluation pipeline in {total_time:.2f}s")
    logger.info(f"[Pipeline] Total baskets evaluated: {portfolio_with_pt['threshold_portfolio_id'].nunique()}")
    logger.info(f"[Pipeline] Baskets meeting PT: {baskets_with_pt_hit['threshold_portfolio_id'].nunique()}")

    return baskets_with_pt_hit

def create_portfolio_profit_target_thresholds(instance):
    """
    Create profit target thresholds for a user's portfolio during an MTF rebalance event.

    This function is triggered when a `Rebalance` instance is saved.
    It inspects the related `user_portfolio` and creates portfolio-level
    profit target thresholds based on user inputs (defined in `portfolio_targets`).

    The thresholds are only created if:
        - The portfolio's `product_type` is MTF.
        - The transaction is not an INITIAL withdrawal.
        - `portfolio_targets` contains a non-empty "profit_target" list.

    Args:
        instance (Rebalance): The Rebalance instance containing `user_portfolio`
            and `user_inputs` (with `portfolio_targets` data).

    Raises:
        Exception: Any unexpected error during threshold creation will be logged
            and re-raised for further handling.

    Example:
        If `portfolio_targets = {"profit_target": [5, 10, 15]}`,
        thresholds for 5%, 10%, and 15% profit will be created.
    """
    logger.info(
        "Starting creation of portfolio profit target thresholds for Rebalance ID: %s",
        getattr(instance, "id", "unknown")
    )

    try:
        user_portfolio = getattr(instance, "user_portfolio", None)
        if not user_portfolio:
            logger.warning(
                "Rebalance instance %s has no associated user_portfolio. Skipping threshold creation.",
                getattr(instance, "id", "unknown")
            )
            return

        if user_portfolio.product_type != ProductTypes.MTF.value:
            logger.debug(
                "Skipping threshold creation for non-MTF portfolio ID: %s (Product Type: %s)",
                user_portfolio.id, user_portfolio.product_type
            )
            return

        if (
            instance.transaction_type == CashTransaction.WITHDRAW.value
            and instance.type == RebalanceTypes.INITIAL.value
        ):
            logger.debug(
                "Skipping threshold creation for withdrawal transaction (Rebalance ID: %s)",
                instance.id
            )
            return

        portfolio_targets = (instance.user_inputs or {}).get("portfolio_targets", {})
        profit_targets = portfolio_targets.get("profit_target", [])

        if not profit_targets:
            logger.info(
                "No profit targets defined in portfolio_targets for Rebalance ID: %s",
                instance.id
            )
            return

        logger.info(
            "Creating %d profit target thresholds for Portfolio ID: %s",
            len(profit_targets),
            user_portfolio.id
        )

        for profit_target in profit_targets:
            if profit_target > 0:
                data = {
                    "portfolio_id": str(user_portfolio.id),
                    "portfolio_type": "user_portfolio",
                    "side": PortfolioSides.LONG,
                    "threshold_type": PortfolioThresholdTypes.PROFIT_TARGET,
                    "status": Status.ACTIVE,
                    "source_id": user_portfolio.user_id,
                    "target_pct": profit_target,
                }
                logger.debug(
                    "Creating profit target threshold: %s%% for portfolio ID: %s",
                    profit_target,
                    user_portfolio.id
                )
                create_user_portfolio_threshold(data)
            else:
                logger.info(f"Skipping creation of portfolio threshold: {profit_target =}")
        logger.info(
            "Successfully created profit target thresholds for Portfolio ID: %s",
            user_portfolio.id
        )

    except Exception as exc:
        logger.info("Error creating portfolio profit target thresholds for Rebalance ID")
        logger.exception(exc)
        raise exc
