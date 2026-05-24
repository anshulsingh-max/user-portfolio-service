"""
    User Portfolio Service
"""
import logging
from typing import List, Dict

from django.db import IntegrityError
from django.db.models import Prefetch

from apps.exceptions.user_portfolio import UserPortfolioNotFound
from apps.holdings.models import Position
from apps.portfolio.constants import InvestmentStatus, RebalanceTransactionTypes, RebalanceTransactionStates, Asset, \
    HoldingStatus
from apps.portfolio.models import UserPortfolio, PortfolioRebalanceTransaction, UserPortfolioRebalance
from apps.portfolio.serializers.user_portfolio import ReadUserPortfolioSerializer
from apps.portfolio.serializers.user_portfolio import UserPortfolioSerializer

logger = logging.getLogger(__name__)


def create_user_portfolio(user_portfolio):
    """Create a new UserPortfolio if it does not already exist.

    This helper first checks whether a portfolio with the same
    ``user_id``, ``subscription_id`` and ``portfolio_id`` is already
    present in the database. If such a record exists, the existing
    instance is returned immediately. Otherwise a new record is created
    via the serializer workflow.
    """
    try:
        logger.info(f"in create user portfolio service {user_portfolio= }")
        ser = UserPortfolioSerializer(data=user_portfolio)
        if ser.is_valid(raise_exception=True):
            instance = ser.save()
            return instance
    except IntegrityError as e:
        logger.error(f"Portfolio already exists. IntegrityError: {e}")
        existing_record = UserPortfolio.objects.get(
            user_id=user_portfolio['user_id'],
            subscription_id=user_portfolio['subscription_id'],
            portfolio_id=user_portfolio['portfolio_id']
        )
        return existing_record


def filter_user_portfolio_on_investment(user_portfolio_queryset, investment_status):
    """
    Takes in UP queryset and investment_status as invested and uninvested
    :param user_portfolio_queryset:
    :param investment_status:
    :return: Returns the queryset according to the investment_status
    """
    logger.info(f"In filter_user_portfolio_on_investment")
    filter_dict = {
        InvestmentStatus.INVESTED.value: [],
        InvestmentStatus.UNINVESTED.value: [],
    }

    for user_portfolio_obj in user_portfolio_queryset.all():
        if user_portfolio_obj.invested_amount:
            filter_dict[InvestmentStatus.INVESTED.value].append(user_portfolio_obj)
        else:
            filter_dict[InvestmentStatus.UNINVESTED.value].append(user_portfolio_obj)
    # logger.info(f"{filter_dict = }")

    return filter_dict[investment_status]


def get_user_portfolios(user_id=None, investment_status=None, broker=None, portfolio_id=None,
                        status='active', subscription_id=None, product_type=None, strategy=None):
    """
    Gets user portfolio depending upon the status and investment amount
    :param status:
    :param user_id:
    :param investment_status:
    :param portfolio_id:
    :param subscription_id:
    :param product_type:
    :param strategy:
    :return:
    """
    logger.info(f"in get user portfolio service {status = } {user_id = }, {investment_status =}, "
                f"{broker =}, {portfolio_id =}, {subscription_id =}, {product_type =}, {strategy =}")
    filters = {
        'user_id': user_id,
        'status': status,
        'portfolio_id': portfolio_id,
        'broker': broker,
        'subscription_id': subscription_id,
        'product_type': product_type,
        'strategy': strategy
    }

    filters = {key: value for key, value in filters.items() if value is not None}

    user_portfolio_queryset = UserPortfolio.objects.filter(**filters).prefetch_related(
        "holdings",
        Prefetch(
            "user_portfolio_rebalances",
            queryset=UserPortfolioRebalance.objects.prefetch_related(
                Prefetch(
                    "portfolio_rebalance_transactions",
                    queryset=PortfolioRebalanceTransaction.objects.prefetch_related("user_instructions")
                )
            )
        )
    )
    # user_portfolio_queryset = UserPortfolio.objects.filter(**filters).prefetch_related("holdings",
    #                                                                                    "user_portfolio_rebalances",
    #                                                                                    "user_portfolio_rebalances__portfolio_rebalance_transactions",
    #                                                                                    "user_portfolio_rebalances__portfolio_rebalance_transactions__user_instructions")

    if investment_status:
        return filter_user_portfolio_on_investment(user_portfolio_queryset, investment_status)

    return user_portfolio_queryset


def compute_holding_status(user_portfolio, cash_carry_forward):
    """
    Derive holding_status based on non-cash holdings quantity and cash carry forward.
    """
    holdings_quantity = sum(
        (holding.quantity or 0)
        for holding in user_portfolio.holdings.all()
        if holding.symbol != Asset.CASH.value
    )

    if holdings_quantity > 0 and cash_carry_forward:
        return HoldingStatus.MULTI_ASSET.value
    if cash_carry_forward and holdings_quantity <= 0:
        return HoldingStatus.CASH.value
    if holdings_quantity > 0 and not cash_carry_forward:
        return HoldingStatus.HOLDINGS.value

    return None


def get_user_portfoliosJTE(user_id=None, investment_status=None, broker=None, portfolio_id=None,
                        status='active', subscription_id=None, product_type=None, strategy=None):
    """
    Gets user portfolio depending upon the status and investment amount
    :param status:
    :param user_id:
    :param investment_status:
    :param portfolio_id:
    :param subscription_id:
    :param product_type:
    :param strategy:
    :return:
    """
    logger.info(f"in get user portfolio service {status = } {user_id = }, {investment_status =}, "
                f"{broker =}, {portfolio_id =}, {subscription_id =}, {product_type =}, {strategy =}")
    filters = {
        'user_id': user_id,
        'status': status,
        'portfolio_id': portfolio_id,
        'broker': broker,
        'subscription_id': subscription_id,
        'product_type': product_type,
        'strategy': strategy
    }

    filters = {key: value for key, value in filters.items() if value is not None}

    user_portfolio_queryset = UserPortfolio.objects.filter(**filters).prefetch_related(
        "holdings",
        Prefetch(
            "user_portfolio_rebalances",
            queryset=UserPortfolioRebalance.objects.prefetch_related(
                Prefetch(
                    "portfolio_rebalance_transactions",
                    queryset=PortfolioRebalanceTransaction.objects.prefetch_related("user_instructions")
                )
            )
        )
    )
    # user_portfolio_queryset = UserPortfolio.objects.filter(**filters).prefetch_related("holdings",
    #                                                                                    "user_portfolio_rebalances",
    #                                                                                    "user_portfolio_rebalances__portfolio_rebalance_transactions",
    #                                                                                    "user_portfolio_rebalances__portfolio_rebalance_transactions__user_instructions")

    if investment_status:
        return filter_user_portfolio_on_investment(user_portfolio_queryset, investment_status)

    return user_portfolio_queryset


def get_user_portfolio(id):
    try:
        logger.info(f"in user portfolio by id service {id = }")
        user_portfolio_obj = UserPortfolio.objects.prefetch_related("holdings",
                                                                    "user_portfolio_rebalances" ,
                                                                    "user_portfolio_rebalances__portfolio_rebalance_transactions",
                                                                    "user_portfolio_rebalances__portfolio_rebalance_transactions__user_instructions").get(id=id)
        return user_portfolio_obj
    except UserPortfolio.DoesNotExist as exc:
        logger.info(f"Data does not exist {id =}")
        logger.exception(exc)
        raise UserPortfolioNotFound(message=f"user portfolio data not found for '{id =}'. ") from exc
    except Exception as exc:
        logger.info(f"Error in get User portfolio by ID")
        logger.exception(exc)
        raise exc


def update_user_portfolio_by_id(data):
    try:
        logger.info(f"in user portfolio update by id service {data = }")
        portfolio_id = data.pop('id')
        UserPortfolio.objects.filter(pk=portfolio_id).update(**data)
        updated_portfolio = UserPortfolio.objects.get(id=portfolio_id)
        return updated_portfolio
    except UserPortfolio.DoesNotExist as exc:
        logger.info(f"user portfolio does not exist")
        logger.exception(exc)
        raise UserPortfolioNotFound(message=f"cannot update portfolio ") from exc
    except Exception as exc:
        logger.info(f"Error in update User portfolio")
        logger.exception(exc)
        raise exc


def update_user_portfolio_by_subscription_id(data):
    try:
        logger.info(f"in user portfolio update by subscription_id service {data = }")
        subscription_id = data.pop('subscription_id')
        portfolio = UserPortfolio.objects.get(subscription_id=subscription_id)
        portfolio.status = data.get("status")
        portfolio.save()
        updated_portfolio = UserPortfolio.objects.get(subscription_id=subscription_id)
        logger.info(f"{updated_portfolio = }")
        return updated_portfolio
    except UserPortfolio.DoesNotExist as exc:
        logger.info(f"user portfolio does not exist")
        logger.exception(exc)
        raise UserPortfolioNotFound(message=f"cannot update portfolio") from exc
    except Exception as exc:
        logger.info(f"Error in update User portfolio")
        logger.exception(exc)
        raise exc


def delete_user_portfolio(id):
    try:
        logger.info(f"In delete_user_portfolio {id = }")
        user_portfolio_obj = UserPortfolio.objects.get(id=id)
        return user_portfolio_obj.delete()
    except UserPortfolio.DoesNotExist as exc:
        logger.info(f"Data does not exist {id =}")
        logger.exception(exc)
        raise UserPortfolioNotFound(message=f"user portfolio data not found for '{id =}'. ") from exc
    except Exception as exc:
        logger.info(f"Error in get User portfolio by ID")
        logger.exception(exc)
        raise exc


def create_latest_rebalance_dict(rebalance_list):
    """
    Create a dictionary containing information about the latest rebalance.

    Parameters:
    - rebalance_list: rebalance objects.

    Returns:
    - dict: A dictionary containing information about the latest rebalance.
    """

    latest_rebalance = {}
    transactions = list(rebalance_list[0].portfolio_rebalance_transactions.all())
    if transactions:
        latest_transaction = max(transactions, key=lambda t: t.id)
    else:
        latest_transaction = None
    latest_rebalance['portfolio_rebalance_id'] = rebalance_list[0].rebalance_id
    latest_rebalance['user_portfolio_rebalance_id'] = rebalance_list[0].id
    latest_rebalance['current_state'] = rebalance_list[0].current_state
    latest_rebalance['type'] = rebalance_list[0].type
    latest_rebalance['reason'] = getattr(rebalance_list[0], 'reason', None)
    latest_rebalance['cash_carry_forward'] = getattr(rebalance_list[0], 'cash_carry_forward', None)
    latest_rebalance['holding_status'] = compute_holding_status(rebalance_list[0].user_portfolio,
                                                                latest_rebalance['cash_carry_forward'])
    latest_rebalance['date'] = rebalance_list[0].created
    latest_rebalance[
        'portfolio_rebalance_transaction'] = latest_transaction.current_state if latest_transaction else latest_transaction
    latest_rebalance['portfolio_rebalance_transaction_type'] = latest_transaction.type if latest_transaction else latest_transaction
    latest_rebalance['user_portfolio_rebalance_transaction_type'] = (
        'initial' if len(rebalance_list) == 1 else rebalance_list[0].transaction_type
        )

    return latest_rebalance


def reset_user_portfolio_of_user(user_id):
    """
    The function is used delete all the user portfolio related data except its subscription to the portfolio.
    Which means user will be subscribed to the portfolio but all the rebalance made and holding will be removed.
    :param user_id:
    :return:
    """
    try:
        logger.info(f"In reset_user_portfolio {user_id = }")
        user_portfolios = UserPortfolio.objects.filter(user_id=user_id)
        user_portfolio_ids = []
        for user_portfolio in user_portfolios:
            user_portfolio_ids.append(user_portfolio.id)
            user_portfolio.id = None
            user_portfolio.save()

        UserPortfolio.objects.filter(id__in=user_portfolio_ids).delete()
        return True
    except Exception as exc:
        logger.info(f"Error in in reseting user portfolio {user_portfolio_ids = }")
        logger.exception(exc)
        raise exc


def get_event_details(rebalance_transaction_id):
    """
    Function to retrieve event details from a given PortfolioRebalanceTransaction ID.
    Filters based on the type ('initial' or 't1') and current_state ('complete').
    Returns user_portfolio_id, username (user_id), subscription_id, and portfolio_id.
    """
    try:
        rebalance_transaction = PortfolioRebalanceTransaction.objects.select_related(
            'portfolio_rebalance__user_portfolio'
        ).get(
            id=rebalance_transaction_id,
            type__in=[RebalanceTransactionTypes.INITIAL.value,
                      RebalanceTransactionTypes.T1.value],
            current_state=RebalanceTransactionStates.COMPLETED.value
        )

        user_portfolio_id = rebalance_transaction.portfolio_rebalance.user_portfolio.id
        username = rebalance_transaction.portfolio_rebalance.user_portfolio.user_id
        subscription_id = rebalance_transaction.portfolio_rebalance.user_portfolio.subscription_id
        portfolio_id = rebalance_transaction.portfolio_rebalance.user_portfolio.portfolio_id

        return {
            "user_portfolio_id": user_portfolio_id,
            "username": username,
            "subscription_id": subscription_id,
            "portfolio_id": portfolio_id
        }

    except PortfolioRebalanceTransaction.DoesNotExist as exc:
        logger.info("Rebalance transaction does not exits")
        logger.exception(exc)
    except Exception as exc:
        logger.info(f"Error while getting event details")
        logger.exception(exc)


def get_user_portfolio_positions_user(user_id, basket_id):
    """
    This function will
    :param user_id:
    :return:
    """
    try:
        logger.info(f"In get user_portfolios holdings {user_id = }")
        if not basket_id:
            return Position.objects.prefetch_related(Prefetch('basket__user_basket')).filter(basket__user_id=user_id, basket__current_state='monitoring')
        return Position.objects.prefetch_related(Prefetch('basket__user_basket')).filter(basket__user_id=user_id, basket_id=basket_id ,basket__current_state='monitoring')
    except Exception as exc:
        logger.info(f"Error in in fetching user portfolio {user_id = }")
        logger.exception(exc)
        raise exc


def fetch_user_portfolio_summary(user_id: str, broker: str, product_type: str) -> List[Dict]:
    """
    Fetches the summary of user portfolios based on the given filters.

    Args:
        user_id (str): The ID of the user.
        broker (str): The associated broker name.
        product_type (str): The type of the product (e.g., 'mtf').

    Returns:
        List[Dict]: A list of dictionaries containing user portfolio summaries, including:
            - user_portfolio_id
            - user_id
            - portfolio_id
            - status
            - is_invested (bool indicating if the portfolio has any non-cash holdings)
            - investment_status (new key representing portfolio investment state)
            - latest_rebalance (dict representing the latest rebalance info)
    """

    filters = {
        "user_id": user_id,
        "broker": broker,
        "product_type": product_type
    }

    logger.info("Fetching user portfolios with filters: %s", filters)

    user_portfolio_queryset = UserPortfolio.objects.filter(**filters).prefetch_related(
        "holdings",
        "user_portfolio_rebalances",
        "user_portfolio_rebalances__portfolio_rebalance_transactions",
        "user_portfolio_rebalances__portfolio_rebalance_transactions__user_instructions"
    )

    logger.info(
        "Found %d portfolios for user_id=%s, broker=%s, product_type=%s",
        len(user_portfolio_queryset), user_id, broker, product_type
    )

    result = []
    total_cash_ingested = 0
    for portfolio in user_portfolio_queryset:
        all_holdings = [
            h for h in portfolio.holdings.all()
            if h.symbol != Asset.CASH.value
        ]
        holdings_positive = [
            {"symbol": h.symbol, "quantity": h.quantity, "avg_buy_price": h.avg_buy_price}
            for h in all_holdings if h.quantity > 0
        ]
        is_invested = len(holdings_positive) > 0

        if not all_holdings:
            investment_status = "not_invested"
        else:
            total_quantity = sum(h.quantity for h in all_holdings)
            investment_status = "active" if total_quantity > 0 else "closed"

        serializer_context = {}
        latest_rebalance = ReadUserPortfolioSerializer(instance=portfolio,
                                                       context=serializer_context).get_latest_rebalance(portfolio)

        logger.info(
            "Portfolio ID %s | User ID %s | Invested: %s | Holdings count: %s | Investment Status: %s",
            portfolio.id, portfolio.user_id, is_invested, len(holdings_positive), investment_status
        )

        result.append({
            "user_portfolio_id": portfolio.id,
            "user_id": portfolio.user_id,
            "portfolio_id": portfolio.portfolio_id,
            "status": portfolio.status,
            "is_invested": is_invested,
            "total_cash_ingested": portfolio.total_cash_ingested,
            "holdings": holdings_positive,
            "investment_status": investment_status,
            "latest_rebalance": latest_rebalance
        })
        total_cash_ingested += portfolio.total_cash_ingested
    logger.info("Total cash ingested: %s", total_cash_ingested)

    logger.info("Returning summary for %d portfolios", len(result))
    return result
