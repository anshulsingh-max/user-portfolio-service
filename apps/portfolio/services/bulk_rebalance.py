import logging
from collections import defaultdict

from apps.portfolio.models import UserPortfolioRebalance
from apps.portfolio.serializers.user_portfolio_rebalance import ReadUserPortfolioRebalanceSerializer

logger = logging.getLogger(__name__)


def get_user_portfolios_rebalances(user_portfolio_ids, current_states=None):
    """Fetch rebalances for multiple user portfolios efficiently.

    Args:
        user_portfolio_ids (List[int]): list of portfolio IDs.
        current_states (Optional[List[str]]): allowed current_state values; if None or empty, no filter.

    Returns:
        Dict[str, List[dict]]: mapping of user_portfolio_id (as string) -> list of rebalance dicts
        (same schema as ReadUserPortfolioRebalanceSerializer used in single endpoint).
    """
    logger.info(
        "Fetching bulk rebalances for portfolios: %s with states: %s",
        user_portfolio_ids,
        current_states,
    )
    qs = UserPortfolioRebalance.objects.filter(
        user_portfolio__in=set(user_portfolio_ids)
    )

    if current_states:
        qs = qs.filter(current_state__in=current_states)

    qs = qs.order_by("id")

    # Avoid N+1 on related transactions and user instructions
    qs = qs.select_related("user_portfolio").prefetch_related(
        "portfolio_rebalance_transactions",
        "portfolio_rebalance_transactions__user_instructions",
    )

    serialized = ReadUserPortfolioRebalanceSerializer(instance=qs, many=True).data

    grouped = defaultdict(list)
    for upr in serialized:
        # upr['user_portfolio'] is the FK id
        grouped[str(upr['user_portfolio'])].append(upr)

    return grouped

