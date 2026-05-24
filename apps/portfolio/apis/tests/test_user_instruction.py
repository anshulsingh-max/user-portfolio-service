"""
    Unit tests for API to for broker app.
"""
import copy
import json

from django.conf import settings
from django.test import TestCase

from apps.portfolio.apis.tests.test_constants import USER_PORTFOLIO_DATA, STATIC_USER_PORTFOLIO_REBALANCE_DATA, \
    PORTFOLIO_REBALANCE_TRANSACTION, TRADE_PLACEMENT_DATA
from apps.portfolio.constants import OrderStatus
from apps.portfolio.models import UserPortfolio, UserInstruction, UserPortfolioRebalance


class TestGetRebalanceTransaction(TestCase):
    """
        Class for unit test
    """

    def setUp(self):
        """
            Does the initial setup
        """
        user_portfolio_instance = UserPortfolio.objects.create(**USER_PORTFOLIO_DATA)

        data = {
            "user_portfolio": user_portfolio_instance.id,
            "type": "rebalance",
            "cash": 0,
            "transaction_type": "rebalance",
            "transaction": None
        }
        data.update(STATIC_USER_PORTFOLIO_REBALANCE_DATA)
        response = self.client.post(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance", data=json.dumps(data),
                                    content_type="application/json")
        user_portfolio_rebalance_id = UserPortfolioRebalance.objects.get(user_portfolio=user_portfolio_instance).id

        data = copy.deepcopy(PORTFOLIO_REBALANCE_TRANSACTION)
        data["user_portfolio_rebalance_id"] = user_portfolio_rebalance_id
        response = self.client.post(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance/transaction",
                                    data=json.dumps(data),
                                    content_type="application/json")

    def test_valid_query_params(self):
        """
            Unit test with valid params
        """
        order_tag = UserInstruction.objects.all().first().order_tag
        data = copy.deepcopy(TRADE_PLACEMENT_DATA)
        data['order_tag'] = order_tag
        response = self.client.put(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance/transaction/"
                                   f"user-instruction", data=data,  content_type="application/json")
        resp = response.json()
        self.assertEqual(resp['error'], False)

        user_instruction_obj = UserInstruction.objects.get(order_tag=order_tag)
        self.assertEqual(user_instruction_obj.status, OrderStatus.FILLED.value)

    def test_invalid_query_params(self):
        """
            Unit test with valid params
        """
        data = copy.deepcopy(TRADE_PLACEMENT_DATA)
        response = self.client.put(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance/transaction/"
                                   f"user-instruction", data=data,  content_type="application/json")
        resp = response.json()
        self.assertEqual(resp['error'], True)
