import logging
from django.core.cache import cache
from django.db.models import Sum, F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from time import perf_counter

from apps.alerts.models import HoldingThreshold
from apps.holdings.models.holdings import Holding
from apps.alerts.models.user_portfolio_threshold import UserPortfolioThreshold
from apps.alerts.constants import (
    PortfolioSides,
    Status,
    ThresholdSource, Asset
)
from apps.portfolio.constants import ProductTypes, RebalanceTypes, CashTransaction, Strategy
from apps.portfolio.models.user_portfolio_rebalance import UserPortfolioRebalance
from apps.utils.cache_lock import acquire_lock, release_lock

logger = logging.getLogger(__name__)
#
#
# @receiver(post_save, sender=Holding)
# def create_or_update_portfolio_threshold(sender, instance, **kwargs):
#     """
#     On Holding save → calculate total portfolio value and
#     create/update UserPortfolioThresholds if portfolio_targets > 0.
#     """
#     logger.info("Creating or updating portfolio threshold for holding %s", instance.id)
#     user_portfolio = instance.user_portfolio
#     if user_portfolio.product_type != ProductTypes.MTF.value:
#         logger.info("Product type is not MTF, skipping")
#         return
#
#     cache_lock_key = f"create_or_update_portfolio_threshold:{user_portfolio.id}"
#     logger.info("Acquiring lock for %s", cache_lock_key)
#     if not acquire_lock(cache_lock_key):
#         logger.info("Another worker holds the lock, skipping")
#         return
#
#     rebalance = (
#         UserPortfolioRebalance.objects
#         .filter(user_portfolio=user_portfolio,
#                 type=RebalanceTypes.INITIAL.value,
#                 transaction_type=CashTransaction.ADD.value
#                 )
#         .order_by("-id")
#         .first()
#     )
#     logger.info("Rebalance: %s", rebalance)
#     if not rebalance or not rebalance.user_inputs:
#         logger.info("No rebalance found")
#         release_lock(cache_lock_key)
#         return
#
#     portfolio_targets = rebalance.user_inputs.get("portfolio_targets", {})
#     if not portfolio_targets:
#         logger.info("No portfolio targets found")
#         release_lock(cache_lock_key)
#         return
#
#     agg = Holding.objects.filter(user_portfolio=user_portfolio).exclude(symbol="cash").aggregate(
#         total_value=Sum(F("quantity") * F("avg_buy_price"))
#     )
#     total_value = agg["total_value"] or 0
#     logger.info("Total value: %s", total_value)
#
#     if total_value <= 0:
#         logger.info("Total value is 0; inactivating ACTIVE portfolio thresholds for portfolio %s", user_portfolio.id)
#         now = timezone.now()
#         (
#             UserPortfolioThreshold.objects
#             .filter(
#                 portfolio_id=str(user_portfolio.id),
#                 portfolio_type="user_portfolio",
#                 status=Status.ACTIVE,
#             )
#             .update(status=Status.INACTIVE, effective_to=now)
#         )
#         release_lock(cache_lock_key)
#         return
#
#     positive_targets_exist = any(
#         any((float(pct) if pct is not None else 0) > 0 for pct in pcts)
#         for pcts in portfolio_targets.values()
#     )
#     if user_portfolio.strategy == Strategy.REBALANCE.value and positive_targets_exist:
#         logger.info("Strategy=REBALANCE; inactivating previous ACTIVE portfolio thresholds before creating new ones")
#         now = timezone.now()
#         (
#             UserPortfolioThreshold.objects
#             .filter(
#                 portfolio_id=str(user_portfolio.id),
#                 portfolio_type="user_portfolio",
#                 status=Status.ACTIVE,
#             )
#             .update(status=Status.INACTIVE, effective_to=now)
#         )
#
#     for threshold_type, values in portfolio_targets.items():
#         logger.info("Threshold type: %s: %s", threshold_type, values)
#         for target_pct in values:
#             try:
#                 pct = float(target_pct)
#             except (TypeError, ValueError):
#                 logger.info("Skipping non-numeric threshold pct: %s", target_pct)
#                 continue
#             logger.info("Processing target_pct: %s", pct)
#             if pct <= 0:
#                 logger.info("Skipping non-positive threshold")
#                 continue
#
#             target_value = total_value + (total_value * pct / 100)
#             target_value = round(target_value, 2)
#             logger.info("Target pct: %s, target value: %s", pct, target_value)
#
#             qs = UserPortfolioThreshold.objects.filter(
#                 portfolio_id=str(user_portfolio.id),
#                 portfolio_type="user_portfolio",
#                 side=PortfolioSides.LONG,
#                 threshold_type=threshold_type,
#                 target_pct=pct,
#             ).order_by("-id")
#
#             threshold = qs.first()
#             created = False
#             if threshold:
#                 updates = {}
#                 if threshold.status != Status.ACTIVE and not getattr(threshold, "effective_to", None):
#                     updates["status"] = Status.ACTIVE
#                     updates["effective_to"] = None
#                 if threshold.target_value != target_value:
#                     updates["target_value"] = target_value
#                 if threshold.source != ThresholdSource.USER or threshold.source_id != str(user_portfolio.user_id):
#                     updates["source"] = ThresholdSource.USER
#                     updates["source_id"] = str(user_portfolio.user_id)
#                 if updates:
#                     for k, v in updates.items():
#                         setattr(threshold, k, v)
#                     threshold.save(update_fields=list(updates.keys()))
#             else:
#                 threshold = UserPortfolioThreshold.objects.create(
#                     portfolio_id=str(user_portfolio.id),
#                     portfolio_type="user_portfolio",
#                     side=PortfolioSides.LONG,
#                     threshold_type=threshold_type,
#                     target_pct=pct,
#                     target_value=target_value,
#                     status=Status.ACTIVE,
#                     effective_to=None,
#                     source=ThresholdSource.USER,
#                     source_id=str(user_portfolio.user_id),
#                 )
#                 created = True
#
#             if not created and threshold.status != Status.ACTIVE and not getattr(threshold, "effective_to", None):
#                 logger.info("Reactivating threshold %s as ACTIVE with new target_value", threshold.id)
#                 threshold.status = Status.ACTIVE
#                 threshold.effective_to = None
#                 threshold.target_value = target_value
#                 threshold.save(update_fields=["status", "effective_to", "target_value"])
#
#     logger.info("Portfolio threshold created/updated for holding %s", instance.id)
#     release_lock(cache_lock_key)
#
#
# @receiver(post_save, sender=UserPortfolioThreshold)
# def update_user_portfolio_threshold(sender, instance: UserPortfolioThreshold, created, **kwargs):
#     """
#     Handles business logic when UserPortfolioThreshold is updated:
#     - Recalculate target_value if target_pct updated.
#     - Set effective_to if status is changed to INACTIVE.
#     """
#     logger.info("In update_user_portfolio_threshold signal")
#     portfolio = UserPortfolio.objects.get(id=int(instance.portfolio_id))
#     if portfolio.product_type != ProductTypes.MTF.value:
#         logger.info("Product type is not MTF, skipping")
#         return
#     try:
#         updates = {}
#         if instance.target_pct is not None:
#             portfolio = UserPortfolio.objects.filter(id=int(instance.portfolio_id)).first()
#             if portfolio and portfolio.invested_amount:
#                 invested_amount = float(portfolio.invested_amount)
#                 target_pct = float(instance.target_pct)
#                 updates["target_value"] = round(invested_amount * (1 + target_pct/ 100), 2)
#                 logger.info(
#                     "Recalculated target_value=%s for UserPortfolioThreshold id=%s",
#                     updates["target_value"], instance.id
#                 )
#             else:
#                 logger.info("No portfolio or invested_amount found for threshold id=%s", instance.id)
#
#         if instance.status == Status.INACTIVE and not instance.effective_to:
#             updates["effective_to"] = timezone.now()
#             logger.info("Set effective_to for UserPortfolioThreshold id=%s", instance.id)
#
#         if updates:
#             UserPortfolioThreshold.objects.filter(id=instance.id).update(**updates)
#             logger.info("Updated UserPortfolioThreshold id=%s with %s", instance.id, updates)
#         logger.info("UserPortfolioThreshold updated for id=%s", instance.id)
#     except Exception as exc:
#         logger.exception("Error handling UserPortfolioThreshold update for id=%s: %s", instance.id, exc)


@receiver(post_save, sender=Holding)
def create_or_update_holding_thresholds(sender, instance: Holding, **kwargs):
    """
    On Holding save → create/update HoldingThresholds.
    One-to-one mapping: each Holding gets thresholds based on rebalance.user_inputs["holding_targets"].
    """

    logger.info("Processing holding thresholds for holding %s", instance.id)
    user_portfolio = instance.user_portfolio
    if user_portfolio.product_type != ProductTypes.MTF.value:
        logger.info("Product type is not MTF, skipping")
        return
    if instance.symbol == Asset.CASH.value:
        logger.info("Skipping cash holding")
        return

    cache_lock_key = f"create_or_update_holding_thresholds:{instance.id}"
    logger.info("Acquiring lock for %s", cache_lock_key)
    if not acquire_lock(cache_lock_key):
        logger.info("Another worker holds the lock for holding %s, skipping", instance.id)
        return

    rebalance = (
        UserPortfolioRebalance.objects
        .filter(user_portfolio=user_portfolio,
                type=RebalanceTypes.INITIAL.value,
                transaction_type=CashTransaction.ADD.value
                )
        .order_by("-id")
        .first()
    )
    if not rebalance or not rebalance.user_inputs:
        logger.info("No rebalance found for portfolio %s", user_portfolio.id)
        release_lock(cache_lock_key)
        return

    holding_targets = rebalance.user_inputs.get("holding_targets", {})
    if not holding_targets:
        logger.info("No holding targets found for holding %s", instance.symbol)
        release_lock(cache_lock_key)
        return

    holding_value = instance.quantity * instance.avg_buy_price
    logger.info("Holding value for %s: %s", instance.symbol, holding_value)

    for threshold_type, values in holding_targets.items():
        logger.info("Threshold type: %s → %s", threshold_type, values)

        for target_pct in values:
            try:
                pct = float(target_pct)
            except (TypeError, ValueError):
                logger.info("Skipping non-numeric threshold pct: %s", target_pct)
                continue
            logger.info("Processing target_pct: %s", pct)
            if pct <= 0:
                logger.info("Skipping non-positive threshold")
                continue

            target_value = holding_value - (holding_value * pct / 100)
            target_value = round(target_value, 2)
            logger.info("Target value: %s", target_value)
            threshold, created = HoldingThreshold.objects.update_or_create(
                holding_id=str(instance.id),
                holding_type="Security",
                side=PortfolioSides.LONG,
                threshold_type=threshold_type,
                status=Status.ACTIVE,
                defaults={
                    "target_value": target_value,
                    "target_pct": pct,
                },
            )
            logger.info(
                "%s threshold %s for holding %s",
                "Created" if created else "Updated",
                threshold.id,
                instance.symbol,
            )
            if threshold.target_value == 0 and threshold.status != Status.INACTIVE:
                threshold.status = Status.INACTIVE
                threshold.effective_to = timezone.now()
                threshold.save(update_fields=["status", "effective_to"])
                logger.info(
                    "Marked threshold %s as INACTIVE because target_value is 0",
                    threshold.id,
                )

    release_lock(cache_lock_key)


@receiver(post_save, sender=HoldingThreshold)
def update_holding_threshold(sender, instance: HoldingThreshold, created, **kwargs):
    """
    Handles business logic when HoldingThreshold is updated:
    - Recalculate target_value if target_pct updated.
    - Set effective_to if status is changed to INACTIVE.
    """
    logger.info("Processing holding threshold update for id=%s", instance.id)
    holding = Holding.objects.filter(id=int(instance.holding_id)).first()
    if holding and holding.user_portfolio.product_type != ProductTypes.MTF.value:
        logger.info(
            "[update_holding_threshold] Skipping: portfolio %s product_type=%s",
            holding.user_portfolio.id,
            holding.user_portfolio.product_type)
        return
    try:
        holding = Holding.objects.filter(id=int(instance.holding_id)).first()
        if not holding:
            logger.warning("No holding found for HoldingThreshold id=%s", instance.id)
            return

        updates = {}

        if instance.target_pct is not None:
            holding_value = holding.quantity * holding.avg_buy_price
            updates["target_value"] = round(holding_value * (1 - instance.target_pct / 100), 2)
            logger.info("Recalculated target_value=%s for id=%s", updates["target_value"], instance.id)

        if instance.status == Status.INACTIVE and not instance.effective_to:
            updates["effective_to"] = timezone.now()
            logger.info("Set effective_to for id=%s", instance.id)

        if updates:
            HoldingThreshold.objects.filter(id=instance.id).update(**updates)
            logger.info("Updated HoldingThreshold id=%s with %s", instance.id, updates)

    except Exception as exc:
        logger.exception("Error handling HoldingThreshold update for id=%s: %s", instance.id, exc)
