"""
    Unit tests for API to for broker app.
"""
import json

from django.conf import settings
from django.test import TestCase

from apps.portfolio.models import UserPortfolio


class TestAddTransaction(TestCase):
    """
        Class for unit test of Add transaction API.
    """
    def setUp(self):
        """
            Does the initial setup
        """
        user_portfolio_data = {
            "user_id": "USR234567890",
            "name": "Admin",
            "portfolio_id": "AISLCT",
        }
        UserPortfolio.objects.create(**user_portfolio_data)

    def test_with_valid_query_params(self):
        """
            Unit test to  Add transaction.
        """
        data = {
            "user_portfolio": UserPortfolio.objects.get(user_id="USR234567890", name="Admin").id,
            "transaction_side": "credit",
            "amount": 100000
        }
        response = self.client.post(f"/{settings.APP_PREFIX}/holding/transaction", data=json.dumps(data),
                                    content_type="application/json")
        resp = response.json()

        self.assertEqual(resp['error'], False)

    def test_with_invalid_id(self):
        """
            Unit test to  Add transaction.
        """
        data = {
            "user_portfolio": 35465778,
            "transaction_side": "credit",
            "amount": 100000
        }
        response = self.client.post(f"/{settings.APP_PREFIX}/holding/transaction", data=json.dumps(data),
                                    content_type="application/json")
        resp = response.json()

        self.assertEqual(resp['error'], True)
