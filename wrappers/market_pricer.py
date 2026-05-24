"""
    Module to make API calls to Market Pricer service.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MarketPricer:
    """
    This class represents a MarketPricer, which is used to retrieve live and end-of-day (EOD) market prices for
    securities.

    Attributes:
        base_url (str): The base URL for the MarketPricer service.
        urls (dict): A dictionary containing the endpoint URLs for live and EOD prices.

    Methods:
        __init__(self, user):
            Initializes a new MarketPricer instance.

            Args:
                service_user (User): The user object representing the authenticated user.

        get_live_prices(self, securities, exchange):
            Retrieves live market prices for a list of securities on a specific exchange.

            Returns:
                list: A list of live market price data for the specified securities.

            Example:
                market_pricer = MarketPricer(user)
                securities = "TCS,RELIANCE"
                exchange = "NSE"
                live_prices = market_pricer.get_live_prices(securities, exchange)
    """

    def __init__(self, service_user):
        logger.info(f"In - MarketPricer {service_user =}")
        self.base_url = settings.MARKET_PRICER_SERVICE
        self.urls = {
            "live": "live"
        }

    def get_live_prices(self, securities, exchange):
        """
        Retrieves live market prices for a list of securities on a specific exchange.

        Args:
            securities (list of str): A list of security symbols for which live prices are requested.
            exchange (str): The exchange on which the securities are traded.

        Returns:
            list: A list of live market price data for the specified securities.

        Example:
            market_pricer = MarketPricer(user)
            securities = "TCS,RELIANCE"
            exchange = "NSE"
            live_prices = market_pricer.get_live_prices(securities, exchange)

        API Endpoint:
            GET /live

        API Parameters:
            - symbols (str): Comma-separated list of security symbols.
            - exchange (str): The exchange on which the securities are traded.

        API Response:
            {
                "data": [
                    {
                        "symbol": "TCS",
                        "price": 150.25,
                        "timestamp": "2023-10-04T10:30:00Z",
                        "exchange": "NSE"
                    },
                    {
                        "symbol": "RELIANCE",
                        "price": 2750.75,
                        "timestamp": "2023-10-04T10:30:00Z",
                        "exchange": "NSE"
                    }
                ]
            }
        """
        logger.info(f"In - get_live_prices {securities =}, {exchange =}")
        market_pricing_live_response = requests.get(url=f"{self.base_url}/{self.urls.get('live')}",
                                                    params={"symbols": securities,
                                                            "exchange": exchange})
        logger.info(f"{market_pricing_live_response =}")
        market_prices_data = market_pricing_live_response.json().get("data")
        return market_prices_data
