"""
    Unit tests for API to for broker app.
"""
import copy
import json

from django.conf import settings
from django.test import TestCase

from apps.holdings.models import Transaction
from apps.portfolio.apis.tests.test_constants import USER_PORTFOLIO_DATA, TRANSACTION_DATA, \
    STATIC_USER_PORTFOLIO_REBALANCE_DATA
from apps.portfolio.constants import States
from apps.portfolio.models import UserPortfolio


class TestAddUserPortfolioRebalance(TestCase):
    """
        Class for unit test
    """

    def setUp(self):
        """
            Does the initial setup
        """
        user_portfolio_instance = UserPortfolio.objects.create(**USER_PORTFOLIO_DATA)

        data = copy.deepcopy(TRANSACTION_DATA)
        data['user_portfolio'] = user_portfolio_instance.id
        response = self.client.post(f"/{settings.APP_PREFIX}/holding/transaction", data=json.dumps(data),
                                    content_type="application/json")

    def test_initial_query_params(self):
        """
            Unit test with valid params
        """
        user_portfolio_id = UserPortfolio.objects.get(user_id="USR4567890", name="Admin").id
        transaction_id = Transaction.objects.get(user_portfolio_id=user_portfolio_id).id

        data = {
            "user_portfolio": user_portfolio_id,
            "type": "initial",
            "cash": 1000000,
            "transaction_type": "add",
            "transaction": transaction_id
        }
        data.update(STATIC_USER_PORTFOLIO_REBALANCE_DATA)
        response = self.client.post(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance", data=json.dumps(data),
                                    content_type="application/json")
        resp = response.json()

        self.assertEqual(resp['error'], False)

    def test_rebalance_query_params(self):
        """
            Unit test with valid params
        """
        user_portfolio_id = UserPortfolio.objects.get(user_id="USR4567890", name="Admin").id

        data = {
            "user_portfolio": user_portfolio_id,
            "type": "rebalance",
            "cash": 0,
            "transaction_type": "rebalance",
            "transaction": None
        }
        data.update(STATIC_USER_PORTFOLIO_REBALANCE_DATA)
        response = self.client.post(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance", data=json.dumps(data),
                                    content_type="application/json")
        resp = response.json()
        self.assertEqual(resp['error'], False)

    def test_invalid_query_params(self):
        """
            Unit test with valid params
        """
        user_portfolio_id = UserPortfolio.objects.get(user_id="USR4567890", name="Admin").id

        data = {
            "user_portfolio": user_portfolio_id,
            "type": "t0",
            "cash": 0,
            "transaction_type": "rebalance",
            "transaction": None
        }
        data.update(STATIC_USER_PORTFOLIO_REBALANCE_DATA)
        response = self.client.post(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance", data=json.dumps(data),
                                    content_type="application/json")
        resp = response.json()
        self.assertEqual(resp['error'], True)


class TestGetUserPortfolioRebalance(TestCase):
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
        response = self.client.get(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance/{user_portfolio_id}?"
                                   f"current_state={States.PENDING.value}")
        resp = response.json()
        print(f"{resp = }")
        self.assertEqual(resp['error'], False)

    def test_invalid_query_params(self):
        """
            Unit test with valid params
        """
        user_portfolio_id = UserPortfolio.objects.get(user_id="USR4567890", name="Admin").id
        response = self.client.get(f"/{settings.APP_PREFIX}/userportfolio/portfolio/rebalance/{user_portfolio_id}?"
                                   f"current_state=vtuyig")
        resp = response.json()
        print(f"{resp = }")
        self.assertEqual(resp['data'], [])
