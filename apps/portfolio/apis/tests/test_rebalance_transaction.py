"""
    Unit tests for API to for broker app.
"""
import copy
import json

from django.conf import settings
from django.test import TestCase
from rest_framework.status import HTTP_404_NOT_FOUND

from apps.portfolio.apis.tests.test_constants import USER_PORTFOLIO_DATA, STATIC_USER_PORTFOLIO_REBALANCE_DATA, \
    PORTFOLIO_REBALANCE_TRANSACTION
from apps.portfolio.models import UserPortfolio, UserPortfolioRebalance, UserInstruction, PortfolioRebalanceTransaction


class TestAddRebalanceTransaction(TestCase):
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

    def test_valid_query_params(self):
        """
            Unit test with valid params
        """
        user_portfolio_id = UserPortfolio.objects.get(user_id="USR4567890", name="Admin").id
        user_portfolio_rebalance_id = UserPortfolioRebalance.objects.get(user_portfolio=user_portfolio_id).id

        data = copy.deepcopy(PORTFOLIO_REBALANCE_TRANSACTION)
        data["user_portfolio_rebalance_id"] = user_portfolio_rebalance_id
        response = self.client.post(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance/transaction",
                                    data=json.dumps(data),
                                    content_type="application/json")
        resp = response.json()
        self.assertEqual(resp['error'], False)
        self.assertEqual(UserInstruction.objects.all().count(), 2)

    def test_invalid_query_params(self):
        """
            Unit test with valid params
        """
        data = copy.deepcopy(PORTFOLIO_REBALANCE_TRANSACTION)
        data["user_portfolio_rebalance_id"] = 12345
        response = self.client.post(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance/transaction",
                                    data=json.dumps(data),
                                    content_type="application/json")
        resp = response.json()
        self.assertEqual(resp['error'], True)
        self.assertEqual(UserInstruction.objects.all().count(), 0)


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
        upt_id = PortfolioRebalanceTransaction.objects.all().first().id
        response = self.client.get(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance/transaction/{upt_id}")
        resp = response.json()
        self.assertEqual(resp['error'], False)
        self.assertEqual(resp['data']['id'], upt_id)

    def test_invalid_query_params(self):
        """
            Unit test with valid params
        """
        response = self.client.get(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance/transaction/123e")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
