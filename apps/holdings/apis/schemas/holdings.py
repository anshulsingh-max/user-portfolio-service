"""
Schemas for transaction requests and responses APIs
"""

from drf_yasg import openapi

holdings_response_schema_dict = {
    "200": openapi.Response(
        description="Transaction Response",
        examples={
            "application/json":
                {
                  "data": [
                    {
                      "user_portfolio": 1,
                      "symbol": "cash",
                      "quantity": 55000
                    },
                    {
                      "user_portfolio": 1,
                      "symbol": "A",
                      "quantity": 20
                    },
                    {
                      "user_portfolio": 1,
                      "symbol": "B",
                      "quantity": 80
                    }
                  ],
                  "error": False,
                  "payload": {}
                }
        }
    )
}

all_users_holdings_response_schema_dict = {
    "200": openapi.Response(
        description="holdings response",
        examples={
            "application/json":
                {
                    "data": {
                        "1": [
                            {
                                "symbol": "HDFCBANK",
                                "quantity": 12.0
                            },
                            {
                                "symbol": "TCS",
                                "quantity": 18.0
                            },
                            {
                                "symbol": "HINDALCO",
                                "quantity": 556.0
                            },
                            {
                                "symbol": "ICICIBANK",
                                "quantity": 275.0
                            },
                            {
                                "symbol": "WIPRO",
                                "quantity": 1110.0
                            },
                            {
                                "symbol": "cash",
                                "quantity": 9500874.1
                            }
                        ]
                    },
                    "error": False,
                    "payload": {}
                }
        }
    )
}
