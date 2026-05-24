"""
    Transaction services module
"""
import logging

from apps.holdings.models import Holding
from apps.portfolio.constants import UserPortfolioStatus, ProductTypes

logger = logging.getLogger(__name__)


def get_user_portfolio_holdings(user_portfolio_id_list):
    """
    Gets user portfolio holdings via user portfolio id
    :param user_portfolio_id_list: pk list
    :return:
    """
    holdings_queryset = Holding.objects.filter(user_portfolio__in=user_portfolio_id_list, quantity__gt=0)
    return holdings_queryset


def get_user_portfolio_holdings_optimized(user_id, broker, product_type):
    """
    Fetches and returns optimized holdings for a user's portfolio based on the provided parameters. It filters
    the holdings associated with the active user portfolio with a quantity greater than zero and includes a
    select_related optimization for the 'user_portfolio'.

    :param user_id: Identifier of the user to fetch portfolio holdings for
    :type user_id: int
    :param broker: Broker associated with the user's portfolio
    :type broker: str
    :param product_type: Type of product associated with the user's portfolio (e.g., equity, mutual fund)
    :type product_type: str
    :return: QuerySet containing filtered and optimized holdings
    :rtype: QuerySet
    """
    logger.info(f"In get user portfolio holdings optimized service {user_id = }, {broker =}, {product_type =}")
    if not product_type:
        logger.info("Product type not provided, defaulting to equity")
        product_type = ProductTypes.EQUITY.value
    holdings_queryset = Holding.objects.filter(user_portfolio__user_id=user_id,
                                               user_portfolio__broker=broker,
                                               user_portfolio__product_type=product_type,
                                               user_portfolio__status=UserPortfolioStatus.ACTIVE.value,
                                               quantity__gt=0).select_related('user_portfolio')
    return holdings_queryset