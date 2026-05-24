import logging
from typing import Dict

from django.db import transaction, router

from apps.alerts.models import HoldingThreshold
from apps.alerts.serializers.holding_threshold import HoldingThresholdSerializer
from apps.alerts.constants import Status

logger = logging.getLogger(__name__)


def create_holding_threshold(validated_data: Dict) -> HoldingThreshold:
    """Create a new HoldingThreshold instance."""
    logger.info("Creating HoldingThreshold", extra={"data": validated_data})
    db_alias = router.db_for_write(HoldingThreshold)
    with transaction.atomic(using=db_alias):
        holding_id = validated_data.get('holding_id')
        holding_type = validated_data.get('holding_type')
        side = validated_data.get('side')
        threshold_type = validated_data.get('threshold_type')
        filters = {
            'holding_id': holding_id,
            'holding_type': holding_type,
            'side': side,
            'threshold_type': threshold_type,
            'status': Status.ACTIVE
        }
        HoldingThreshold.objects.filter(**filters).update(status=Status.INACTIVE)
        serializer = HoldingThresholdSerializer(data=validated_data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        logger.info("Created HoldingThreshold", extra={"id": instance.id})
        return instance


def update_holding_threshold(threshold_id: int, update_data: Dict) -> HoldingThreshold:
    """
    Update an existing HoldingThreshold instance with provided fields.
    The post_save signal handles recalculation of target_value and effective_to.

    Args:
        threshold_id (int): ID of the HoldingThreshold to update.
        update_data (dict): Fields to update (partial update allowed).

    Returns:
        HoldingThreshold: The updated instance.
    """
    try:
        db_alias = router.db_for_write(HoldingThreshold)
        with transaction.atomic(using=db_alias):
            threshold = HoldingThreshold.objects.using(db_alias).get(id=threshold_id)
            logger.info("Updating HoldingThreshold", extra={"id": threshold_id, "data": update_data})
            for field, value in update_data.items():
                if field != "id" and value is not None:
                    setattr(threshold, field, value)

            threshold.save(using=db_alias)
            logger.info("Successfully updated HoldingThreshold id=%s", threshold_id)
            return threshold

    except HoldingThreshold.DoesNotExist as exc:
        logger.error("HoldingThreshold not found with id=%s", threshold_id, exc_info=exc)
        raise
    except Exception as exc:
        logger.error("Error updating HoldingThreshold id=%s", threshold_id, exc_info=exc)
        raise


def fetch_holding_thresholds(filters: Dict):
    """Return a queryset of ``HoldingThreshold`` filtered according to provided params.

    The logic mirrors the previous implementation inside
    `apps.alerts.apis.holding_threshold.HoldingThresholdView.get` but now lives
    in the service layer so the API remains a thin controller.

    Parameters
    ----------
    filters : Dict
        Validated filters from `HoldingThresholdQueryParamsValidator`.

    Returns
    -------
    django.db.models.QuerySet[HoldingThreshold]
        Ordered queryset ready for serialisation.
    """
    try:
        logger.info("Fetching HoldingThresholds in service layer", extra={"filters": filters})

        base_filters = filters.copy()
        source_id = base_filters.pop("source_id", None)
        holding_id_param = base_filters.pop("holding_id", None)

        queryset = HoldingThreshold.objects.filter(**base_filters)

        if source_id:
            from apps.alerts.models import UserPortfolioThreshold  # local import to avoid circular
            from apps.holdings.models import Holding

            portfolio_ids = (
                UserPortfolioThreshold.objects.filter(source_id=source_id)
                .values_list("portfolio_id", flat=True)
            )

            holding_ids = (
                Holding.objects.filter(user_portfolio_id__in=portfolio_ids)
                .exclude(symbol="cash")
                .values_list("symbol", flat=True)
                .distinct()
            )

            queryset = queryset.filter(holding_id__in=holding_ids)

        if holding_id_param:
            queryset = queryset.filter(holding_id=holding_id_param)

        queryset = queryset.order_by("-effective_from")
        return queryset
    except Exception as exc:
        logger.error("Error fetching HoldingThresholds in service", exc_info=exc)
        raise
