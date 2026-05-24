"""
    User instruction service
"""
import logging

from apps.alerts.constants import Status, PortfolioThresholdTypes
from apps.alerts.models import UserPortfolioThreshold
from apps.portfolio.constants import USER_PORTFOLIO
from apps.portfolio.models.user_portfolio import UserPortfolio

logger = logging.getLogger(__name__)


def get_active_thresholds_for_user(user_id):
    """
        Iterates through the thresholds and gives a cumulative list for user
        :param user_id:
        :return:
    """
    from django.db.models.functions import Cast
    from django.db.models import CharField

    thresholds = UserPortfolioThreshold.objects.filter(
        portfolio_type=USER_PORTFOLIO,
        status=Status.ACTIVE,
        threshold_type=PortfolioThresholdTypes.PROFIT_TARGET,
        portfolio_id__in=UserPortfolio.objects.filter(user_id=user_id).annotate(
            id_str=Cast('id', CharField())
        ).values('id_str')
    )
    return list(thresholds)