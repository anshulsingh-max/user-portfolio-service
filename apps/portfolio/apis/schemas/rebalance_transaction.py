"""
Schemas for transaction requests and responses APIs
"""

from drf_yasg import openapi

rebalance_transaction_request_schema_dict = openapi.Schema(
    title="Initialize Rebalance Transaction",
    type=openapi.TYPE_OBJECT,
    properties={
        "user_portfolio_rebalance_id": openapi.Schema(type=openapi.TYPE_INTEGER,
                                                      description='Portfolio Rebalance ID', example=1),
        "allocation_quantity": openapi.Schema(type=openapi.TYPE_ARRAY, description=("Quantity calculated on "
                                                                                     "user defined weights"),
                                                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                              example=[
                                                  {
                                                      "symbol": "A",
                                                      "quantity": 10,
                                                      "side": "buy",
                                                      "asm_consent": True,
                                                      "asm_reason": ""
                                                  },
                                                  {
                                                      "symbol": "B",
                                                      "quantity": 20,
                                                      "side": "buy",
                                                      "asm_consent": True,
                                                      "asm_reason": ""
                                                  }
                                              ]),
        "rebalance_json": openapi.Schema(type=openapi.TYPE_OBJECT, description=("Rebalance json from "
                                                                                "rebalance service"),
                                         example={})
    }
)

user_portfolio_rebalance_transaction_response_schema_dict = {
    "200": openapi.Response(
        description="User portfolio rebalance Response",
        examples={
            "application/json": {
                "data": {
                    "id": 12,
                    "portfolio_rebalance": 2,
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
                    "user_rebalance_json": {},
                    "type": "initial",
                    "current_state": "processing",
                    "executed_list": None,
                    "amount": 0,
                    "user_instructions": [
                        {
                            "id": 12,
                            "portfolio_rebalance_transaction": 12,
                            "trade_placement_id": None,
                            "order_tag": "9529fb9a-d0d2-45f3-b028-50bab4bba7d6",
                            "symbol": "A",
                            "quantity": 10,
                            "side": "buy",
                            "value": None,
                            "status": "waiting",
                            "created": "2023-10-29T20:00:04.668441Z",
                            "modified": "2023-10-29T20:00:04.668455Z"
                        },
                        {
                            "id": 13,
                            "portfolio_rebalance_transaction": 12,
                            "trade_placement_id": None,
                            "order_tag": "4ead15fe-07ba-46a1-b30d-73510436aec9",
                            "symbol": "B",
                            "quantity": 20,
                            "side": "buy",
                            "value": None,
                            "status": "waiting",
                            "created": "2023-10-29T20:00:04.674103Z",
                            "modified": "2023-10-29T20:00:04.674115Z"
                        }
                    ]
                },
                "error": False,
                "payload": {
                    "user_portfolio_rebalance_id": 2,
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
            }
        }
    )
}

get_portfolio_rebalance_transaction_schema_dict = {
    "200": openapi.Response(
        description="User portfolio rebalance Response",
        examples={
            "application/json": {
                "data": {
                    "id": 13,
                    "portfolio_rebalance": 3,
                    "allocation_quantity": [
                        {
                            "side": "buy",
                            "symbol": "A",
                            "quantity": 10
                        },
                        {
                            "side": "buy",
                            "symbol": "B",
                            "quantity": 20
                        }
                    ],
                    "user_rebalance_json": [
                        {
                            "side": "buy",
                            "symbol": "A",
                            "quantity": 10
                        },
                        {
                            "side": "buy",
                            "symbol": "B",
                            "quantity": 20
                        }
                    ],
                    "type": "initial",
                    "current_state": "completed",
                    "executed_list": [
                        "[1",
                        "2]"
                    ],
                    "amount": 0,
                    "user_instructions": [
                        {
                            "id": 14,
                            "portfolio_rebalance_transaction": 13,
                            "trade_placement_id": 1,
                            "order_tag": "d8a55c25-d3ff-429e-b6e3-d68d57592ab9",
                            "symbol": "A",
                            "quantity": 10,
                            "side": "buy",
                            "value": 5000,
                            "status": "filled",
                            "created": "2023-10-29T20:15:57.445715Z",
                            "modified": "2023-10-29T20:21:55.384406Z"
                        },
                        {
                            "id": 15,
                            "portfolio_rebalance_transaction": 13,
                            "trade_placement_id": 2,
                            "order_tag": "ce0b3f4a-7852-4b33-a0b1-663513693528",
                            "symbol": "B",
                            "quantity": 20,
                            "side": "buy",
                            "value": 5000,
                            "status": "filled",
                            "created": "2023-10-29T20:15:57.452272Z",
                            "modified": "2023-10-30T09:15:25.272032Z"
                        }
                    ]
                },
                "error": False,
                "payload": {}
            }
        }
    )
}

update_portfolio_transaction_schema_dict = {
    "200": openapi.Response(
        description="Update portfolio rebalance transaction Response",
        examples={
            "application/json": {
                "data": {"id": 1},
                "error": False,
                "payload": {}
            }
        }
    )
}

update_portfolio_transaction_request_schema_dict = openapi.Schema(
    title="Initialize Rebalance Transaction",
    type=openapi.TYPE_OBJECT,
    properties={
        "allocation_quantity": openapi.Schema(type=openapi.TYPE_OBJECT, description=("Quantity calculated on "
                                                                                     "user defined weights"),
                                              example=[
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
                                              ]),
        "rebalance_json": openapi.Schema(type=openapi.TYPE_OBJECT, description=("Rebalance json from "
                                                                                "rebalance service"),
                                         example={}),
        "current_state": openapi.Schema(type=openapi.TYPE_STRING, description="Transaction State",
                                        example="processing"),
        "type": openapi.Schema(type=openapi.TYPE_STRING, description="Rebalance Type",
                               example="t0"),
    }
)
