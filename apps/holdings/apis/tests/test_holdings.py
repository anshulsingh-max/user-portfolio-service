"""
    Unit tests for API to for broker app.
"""
import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from apps.portfolio.constants import Asset
from apps.portfolio.models import UserPortfolio


class TestGetHolding(TestCase):
    """
        Class for unit test of Get Holdings details
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
        user_portfolio_instance = UserPortfolio.objects.create(**user_portfolio_data)

        data = {
            "user_portfolio": user_portfolio_instance.id,
            "transaction_side": "credit",
            "amount": 100000
        }
        response = self.client.post(f"/{settings.APP_PREFIX}/holding/transaction", data=json.dumps(data),
                                    content_type="application/json")

    def test_with_valid_query_params(self):
        """
            Unit test with valid params
        """
        user_portfolio_id = UserPortfolio.objects.get(user_id="USR234567890", name="Admin").id
        response = self.client.get(f"/{settings.APP_PREFIX}/holding/holdings/{user_portfolio_id}")
        resp = response.json()

        self.assertEqual(resp['error'], False)
        self.assertEqual(resp['data'][0]['user_portfolio'], user_portfolio_id)
        self.assertEqual(resp['data'][0]['symbol'], Asset.CASH.value)
        self.assertEqual(resp['data'][0]['quantity'], 100000)

    def test_with_invalid_query_params(self):
        """
            Unit test with invalid params
        """
        response = self.client.get(f"/{settings.APP_PREFIX}/holding/holdings/65")
        resp = response.json()

        self.assertEqual(resp['error'], False)
        self.assertEqual(len(resp['data']), 0)
