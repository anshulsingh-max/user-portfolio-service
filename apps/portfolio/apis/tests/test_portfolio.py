"""
    Unit tests for API to for broker app.
"""
import json

from django.conf import settings
from django.test import TestCase
from rest_framework.status import HTTP_404_NOT_FOUND

from apps.portfolio.apis.tests.test_constants import USER_PORTFOLIO_DATA, USER_PORTFOLIO_DATA_2
from apps.portfolio.constants import UserPortfolioStatus
from apps.portfolio.models import UserPortfolio


class TestPortfolioAdd(TestCase):
    """
        Class for unit test of Add Portfolio
    """
    def test_with_valid_query_params(self):
        """
            Unit test to  Add portfolio
        """
        response = self.client.post(f"/{settings.APP_PREFIX}/userportfolio/portfolio",
                                    data=json.dumps(USER_PORTFOLIO_DATA),
                                    content_type="application/json")
        resp = response.json()

        self.assertEqual(resp['error'], False)
        self.assertIsInstance(resp['data']['id'], int)


class TestGetPortfolio(TestCase):
    """
        Class for unit test
    """

    def setUp(self):
        """
            Does the initial setup
        """
        UserPortfolio.objects.create(**USER_PORTFOLIO_DATA)

    def test_with_valid_query_params(self):
        """
            Unit test with valid params
        """
        user_portfolio_id = UserPortfolio.objects.get(user_id=USER_PORTFOLIO_DATA['user_id'], name="Admin").id
        response = self.client.get(f"/{settings.APP_PREFIX}/userportfolio/portfolio/{user_portfolio_id}")
        resp = response.json()

        self.assertEqual(resp['error'], False)
        self.assertEqual(resp['data']['user_id'], "USR4567890")
        self.assertEqual(resp['data']['name'], "Admin")

    def test_with_invalid_query_params(self):
        """
            Unit test with invalid params
        """
        user_portfolio_id = 4356789
        response = self.client.get(f"/{settings.APP_PREFIX}/userportfolio/portfolio/{user_portfolio_id}")
        resp = response.json()

        self.assertEqual(resp['error'], True)


class TestGetPortfolioList(TestCase):
    """
        Class for unit test
    """

    def setUp(self):
        """
            Does the initial setup
        """
        UserPortfolio.objects.create(**USER_PORTFOLIO_DATA)
        UserPortfolio.objects.create(**USER_PORTFOLIO_DATA_2)

    def test_with_active_query_params(self):
        """
            Unit test with active params
        """
        response = self.client.get(f"/{settings.APP_PREFIX}/userportfolio/portfolio?user_id="
                                   f"{USER_PORTFOLIO_DATA['user_id']}&status={UserPortfolioStatus.ACTIVE.value}"
                                   f"&broker={USER_PORTFOLIO_DATA['broker']}")
        resp = response.json()

        self.assertEqual(resp['error'], False)
        self.assertEqual(resp['data'][0]['user_id'], USER_PORTFOLIO_DATA['user_id'])
        self.assertEqual(resp['data'][0]['portfolio_id'], USER_PORTFOLIO_DATA['portfolio_id'])

    def test_with_inactive_query_params(self):
        """
            Unit test with inactive params
        """
        response = self.client.get(f"/{settings.APP_PREFIX}/userportfolio/portfolio?user_id="
                                   f"{USER_PORTFOLIO_DATA_2['user_id']}&status={UserPortfolioStatus.INACTIVE.value}"
                                   f"&broker={USER_PORTFOLIO_DATA_2['broker']}")
        resp = response.json()

        self.assertEqual(resp['error'], False)
        self.assertEqual(resp['data'][0]['user_id'], USER_PORTFOLIO_DATA_2['user_id'])
        self.assertEqual(resp['data'][0]['portfolio_id'], USER_PORTFOLIO_DATA_2['portfolio_id'])

    def test_with_invalid_query_params(self):
        """
            Unit test with inactive params
        """
        response = self.client.get(f"/{settings.APP_PREFIX}/userportfolio/portfolio?user_id="
                                   f"{USER_PORTFOLIO_DATA['user_id']}&status=5e46dfu&broker={USER_PORTFOLIO_DATA['broker']}")
        resp = response.json()

        self.assertEqual(resp['error'], True)


class TestUpdatePortfolio(TestCase):
    """
        Class for unit test
    """

    def setUp(self):
        """
            Does the initial setup
        """
        UserPortfolio.objects.create(**USER_PORTFOLIO_DATA)

    def test_with_valid_query_params(self):
        """
            Unit test with valid params
        """
        data = {
            "status": UserPortfolioStatus.INACTIVE.value
        }
        user_portfolio_id = UserPortfolio.objects.get(user_id=USER_PORTFOLIO_DATA['user_id'],
                                                      name=USER_PORTFOLIO_DATA['name']).id
        response = self.client.put(f"/{settings.APP_PREFIX}/userportfolio/portfolio/{user_portfolio_id}",
                                   data=json.dumps(data),
                                   content_type="application/json")
        resp = response.json()
        self.assertEqual(resp['error'], False)

        user_portfolio_obj = UserPortfolio.objects.get(id=user_portfolio_id)
        self.assertEqual(user_portfolio_obj.status, UserPortfolioStatus.INACTIVE.value)

    def test_with_invalid_query_params(self):
        """
            Unit test with invalid params
        """
        data = {
            "status": "64f75g"
        }
        user_portfolio_id = UserPortfolio.objects.get(user_id=USER_PORTFOLIO_DATA['user_id'],
                                                      name=USER_PORTFOLIO_DATA['name']).id
        response = self.client.put(f"/{settings.APP_PREFIX}/userportfolio/portfolio/{user_portfolio_id}",
                                   data=json.dumps(data),
                                   content_type="application/json")
        resp = response.json()
        self.assertEqual(resp['error'], True)

    def test_with_invalid_id(self):
        """
            Unit test with invalid params
        """
        data = {
            "status": "6475"
        }
        user_portfolio_id = "f65yuyfthyi"
        response = self.client.put(f"/{settings.APP_PREFIX}/userportfolio/portfolio/{user_portfolio_id}",
                                   data=json.dumps(data),
                                   content_type="application/json")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
