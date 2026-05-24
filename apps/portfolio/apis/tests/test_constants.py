"""
    Constants file for all the tests
"""

USER_PORTFOLIO_DATA = {
    "user_id": "USR4567890",
    "name": "Admin",
    "portfolio_id": "AISLCT",
    "status": "active",
    "subscription_id": "AI1287ad",
    "broker": "paper_trade"
  }

USER_PORTFOLIO_DATA_2 = {
    "user_id": "USR4567890",
    "name": "Admin",
    "portfolio_id": "AISLCT2",
    "status": "inactive",
    "broker": "paper_trade"
  }

STATIC_USER_PORTFOLIO_REBALANCE_DATA = {
            "rebalance_id": 1,
            "user_inputs": [
                {
                    "symbol": "A",
                    "weight": 0.1
                },
                {
                    "symbol": "B",
                    "weight": 0.1
                }
            ],
        }

PORTFOLIO_REBALANCE_TRANSACTION = {
    "allocation_quantity": [
        {
            "symbol": "A",
            "quantity": 10,
            "side": "buy"
        },
        {
            "symbol": "B",
            "quantity": 20,
            "side": "buy"
        }
    ],
    "rebalance_json": {}
}

TRANSACTION_DATA = {
            "transaction_side": "credit",
            "amount": 100000
        }

TRADE_PLACEMENT_DATA = {
            "trade_placement_id": 1,
            "order_tag": "order_tag",
            "symbol": "HDFCBANK",
            "quantity": 1,
            "filled_quantity": 1,
            "side": "buy",
            "value": 1000,
            "status": "filled"
        }