import logging

from django.conf import settings

from wrappers.api_client import APIClient

logger = logging.getLogger(__name__)


class PortfolioBusiness(APIClient):
    """
    Class for making API calls to the User Portfolio Service.

    Args:
    user (str): The user for whom the API calls are being made.
    """

    def __init__(self):
        """
        Initialize the UserPortfolio object.

        Args:
        user (str): The user for whom the API calls are being made.
        """
        super().__init__("user_portfolio_business")
        self.base_url = settings.PORTFOLIO_BUSINESS_URL
        self.api_key = settings.PORTFOLIO_BUSINESS_API_KEY
        self.urls = {
            "portfolio": "portfolio",
            "benchmark_performance": "index/{}/performance",
            "active_model_by_id":"model"
            }

    def portfolio_details(self, portfolio_id, headers=None):
        """
        Get user portfolios

        Args:
        user_id (str): The Id of the User
        status (str): status of the portfolio

        Returns:
        Array: user Portfolios
        """
        logger.info(f"In - get portfolio details {portfolio_id = }")
        data = self._get(url=f"{self.base_url}/{self.urls.get('portfolio')}/{portfolio_id}", headers=headers)
        if data:
            return data.get("data")

    def benchmark_performance(self, benchmark_name, headers=None):
        """
        Fetches the performance details of a specified benchmark.

        This method logs the process of getting portfolio details and
        fetches the performance data for the given benchmark name using
        a GET request. It then logs the retrieved data and returns the
        relevant data portion.

        Args:
            benchmark_name (str): The name of the benchmark whose performance details are to be fetched.
            headers (dict): A dictionary containing the headers to be sent with the GET request.

        Returns:
            dict: The 'data' part of the response containing the benchmark performance details.

        Logs:
            Logs the process of getting the portfolio details and the fetched data.
        """
        logger.info(f"In - get portfolio details {benchmark_name = }")
        data = self._get(url=f"{self.base_url}/{self.urls.get('benchmark_performance').format(benchmark_name)}",
                         headers=headers)
        logger.info(f"{data = }")
        if data:
            return data.get("data")

    def active_model_by_id(self, portfolio_id, broker, product_type="MTF" ,  headers=None):
        """
        Fetches the active model details for a given model ID.

        This method logs the process of getting active model details and
        fetches the data for the specified model ID using a GET request.
        It then logs the retrieved data and returns the relevant data portion.

        Args:
            portfolio_id (str): The ID of the model whose active details are to be fetched.
            headers (dict): A dictionary containing the headers to be sent with the GET request.
        """
        logger.info(f"In - get active model details {portfolio_id = }")
        headers = headers or {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        params = {
            "broker": broker,
            "product_type": product_type,
            "status": "active"
        }
        data = self._get(url=f"{self.base_url}/{self.urls.get('active_model_by_id')}/{portfolio_id}",
                         headers=headers, params=params)
        logger.info(f"Fetched active model details for portfolio_id={portfolio_id}, broker={broker}, product_type={product_type}")
        logger.debug(f"Response data: {data}")
        if data:
            return data.get("data")
