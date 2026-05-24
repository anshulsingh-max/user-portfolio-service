"""
Schemas for transaction requests and responses APIs
"""

from drf_yasg import openapi

from apps.portfolio.constants import RebalanceTypes, CashTransaction, States, RebalanceTransactionTypes, \
    RebalanceTransactionStates

user_portfolio_rebalance_request_schema_dict = openapi.Schema(
    title="Initialize Transaction",
    type=openapi.TYPE_OBJECT,
    properties={
                  "user_portfolio": openapi.Schema(type=openapi.TYPE_INTEGER, description='User Portfolio ID',
                                                   example=1),
                  "type": openapi.Schema(type=openapi.TYPE_STRING, description=('What kind of rebalance it is '
                                                                                'initial or rebalance'),
                                         example=RebalanceTypes.INITIAL.value, enum=[RebalanceTypes.REBALANCE.value,
                                         RebalanceTypes.INITIAL.value]),
                  "rebalance_id": openapi.Schema(type=openapi.TYPE_INTEGER, description='Portfolio rebalance id',
                                                 example=1),
                  "user_inputs": openapi.Schema(type=openapi.TYPE_OBJECT, description="User defined weights",
                                                example=[
                                                            {
                                                              "symbol": "A",
                                                              "weight": 0.1
                                                            },
                                                            {
                                                              "symbol": "B",
                                                              "weight": 0.1
                                                            }
                                                          ]),
                  "cash": openapi.Schema(type=openapi.TYPE_NUMBER, description="Cash being added or withdrawn",
                                         example=1000),
                  "transaction_type": openapi.Schema(type=openapi.TYPE_STRING, description=("Type of cash transaction "
                                                                                            "eg. it is initial "
                                                                                            "investement or addition"),
                                                     example=CashTransaction.REBALANCE.value,
                                                     enum=[CashTransaction.REBALANCE.value, CashTransaction.ADD.value,
                                                           CashTransaction.WITHDRAW.value]),
                  "transaction": openapi.Schema(type=openapi.TYPE_INTEGER, description=("Relevant transaction id in "
                                                                                          "case of addition and "
                                                                                          "withdrawal"), example=1),
                  "proxy": openapi.Schema(type=openapi.TYPE_STRING, description="Proxy for the user. User/Dealer",
                                          example='user'),
                  "instruction_url": openapi.Schema(type=openapi.TYPE_STRING,
                                                    description="S3 file url for instructions.")
    }
)

user_portfolio_rebalance_response_schema_dict = {
    "200": openapi.Response(
        description="User portfolio rebalance Response",
        examples={
            "application/json":
                {
                  "data": {
                    "user_portfolio_rebalance_id": 7
                  },
                  "error": False,
                  "payload": {
                                  "user_portfolio_id": 1,
                                  "type": "initial",
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
                                  "cash": 1000,
                                  "transaction_type": "add",
                                  "transaction_id": 1,
                                  "allocation_quantity": [
                                    {
                                      "symbol": "A",
                                      "quantity": 10
                                    },
                                    {
                                      "symbol": "B",
                                      "quantity": 20
                                    }
                                  ],
                                  "rebalance_json": {},
                                }
                }
        }
    )
}

get_user_portfolio_rebalance_request_schema_dict = [
    openapi.Parameter(name='current_state', in_=openapi.IN_QUERY, description='Current state of rebalance',
                      example=f"Send in ',' separated values for multiple statuses such as: "
                              f"{States.COMPLETE.value},{States.PENDING.value},{States.PARTIAL.value}",
                      type=openapi.TYPE_STRING),
]

get_user_portfolio_rebalance_response_schema_dict = {
    "200": openapi.Response(
        description="User portfolio rebalance Response",
        examples={
            "application/json":
                {
                    "data": [
                        {
                            "user_portfolio": 1,
                            "type": "initial",
                            "states": [
                                "pending",
                                "complete"
                            ],
                            "current_state": "complete",
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
                            "cash_ingested": 0,
                            "transaction_type": "rebalance",
                            "transaction": 2,
                            "created": "2023-10-29T20:15:05.080205Z",
                            "modified": "2023-10-30T18:17:09.173065Z"
                        }
                    ],
                    "error": False,
                    "payload": {
                        "current_state": "complete"
                    }
                }
        }
    )
}

get_user_rebalance_orders_request_schema_dict = [
    openapi.Parameter(name='type', description='Type of rebalance transaction', type=openapi.TYPE_STRING,
                      example=f"{RebalanceTransactionTypes.INITIAL.value},{RebalanceTransactionTypes.T0.value},"
                              f"{RebalanceTransactionTypes.T1.value}", in_=openapi.IN_QUERY,),
    openapi.Parameter(name='user_portfolio_rebalance_id', description='Rebalance id of user portfolio',
                      type=openapi.TYPE_INTEGER, example=1, in_=openapi.IN_QUERY,),
]

get_user_rebalance_response_schema_dict = {
    "200": openapi.Response(
        description="User portfolio rebalance Response",
        examples={
            "application/json":
            {
                "data": {
                    "orders": [
                        {
                            "id": 1542,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2490,
                            "order_tag": "7c87e631-fda0-4a0f-a048-198a50a89414",
                            "symbol": "ADANIENT",
                            "quantity": 4,
                            "side": "buy",
                            "value": 8906.6,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.155901Z",
                            "modified": "2023-11-21T09:14:12.673706Z"
                        },
                        {
                            "id": 1543,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2486,
                            "order_tag": "fa4f8e2c-af72-4df8-afe4-0f9a0e505612",
                            "symbol": "APOLLOHOSP",
                            "quantity": 1,
                            "side": "buy",
                            "value": 5474.9,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.160010Z",
                            "modified": "2023-11-21T09:14:11.882527Z"
                        },
                        {
                            "id": 1544,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2488,
                            "order_tag": "35c1f09a-2b94-41ed-b974-550ad04da729",
                            "symbol": "BRITANNIA",
                            "quantity": 2,
                            "side": "buy",
                            "value": 9362.6,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.164075Z",
                            "modified": "2023-11-21T09:14:12.284212Z"
                        },
                        {
                            "id": 1545,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2489,
                            "order_tag": "a5344ccf-380b-4ce4-b7f9-52a56dec46f7",
                            "symbol": "EICHERMOT",
                            "quantity": 2,
                            "side": "buy",
                            "value": 7663.6,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.168578Z",
                            "modified": "2023-11-21T09:14:12.620293Z"
                        },
                        {
                            "id": 1546,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2495,
                            "order_tag": "65e1f2f0-d980-4386-80aa-4aa855348d94",
                            "symbol": "HINDALCO",
                            "quantity": 19,
                            "side": "buy",
                            "value": 9674.8,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.172530Z",
                            "modified": "2023-11-21T09:14:13.119264Z"
                        },
                        {
                            "id": 1547,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2491,
                            "order_tag": "2c291afe-ac52-4ffa-b20e-67883b81b5db",
                            "symbol": "INDUSINDBK",
                            "quantity": 6,
                            "side": "buy",
                            "value": 8986.5,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.176643Z",
                            "modified": "2023-11-21T09:14:12.744622Z"
                        },
                        {
                            "id": 1548,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2492,
                            "order_tag": "9bd38bf3-03cd-46a2-83e2-61eeaac442f4",
                            "symbol": "SBILIFE",
                            "quantity": 7,
                            "side": "buy",
                            "value": 9935.800000000001,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.180721Z",
                            "modified": "2023-11-21T09:14:13.023159Z"
                        },
                        {
                            "id": 1549,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2493,
                            "order_tag": "bada5d8b-c56d-4bfe-9ba4-f6cf0783debe",
                            "symbol": "TECHM",
                            "quantity": 8,
                            "side": "buy",
                            "value": 9638.8,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.184737Z",
                            "modified": "2023-11-21T09:14:12.973064Z"
                        },
                        {
                            "id": 1550,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2487,
                            "order_tag": "026f12b7-95e3-43a7-92cc-5d052430f3f3",
                            "symbol": "LTIM",
                            "quantity": 1,
                            "side": "buy",
                            "value": 5571.95,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.188710Z",
                            "modified": "2023-11-21T09:14:12.039691Z"
                        },
                        {
                            "id": 1551,
                            "portfolio_rebalance_transaction": 167,
                            "trade_placement_id": 2494,
                            "order_tag": "e27b707d-121b-47f2-8728-0a27715398a5",
                            "symbol": "TATAMOTORS",
                            "quantity": 14,
                            "side": "buy",
                            "value": 9472.4,
                            "status": "filled",
                            "created": "2023-11-21T09:14:11.192587Z",
                            "modified": "2023-11-21T09:14:13.071794Z"
                        }
                    ],
                    "invested_amount": 101010101,
                    "remaining_amount": 101010101
                },
                "error": False,
                "payload": {
                    "type": "initial",
                    "user_portfolio_rebalance_id": "145"
                }
            }
        }
    )
}


update_user_portfolio_rebalance_request_schema_dict = openapi.Schema(
    title="Update user portfolio rebalance",
    type=openapi.TYPE_OBJECT,
    properties={
                  "transaction": openapi.Schema(type=openapi.TYPE_INTEGER, description='Holding transaction id',
                                                example=1),
                  "cash_ingested": openapi.Schema(type=openapi.TYPE_NUMBER, description='Cash processed',
                                                  example=23456789),
                  "instruction_url": openapi.Schema(type=openapi.TYPE_STRING,
                                          description="S3 file url for instructions.")
    }
)


manually_complete_query_params = openapi.Schema(
    title="Manually Complete Rebalance Transaction",
    type=openapi.TYPE_OBJECT,
    properties={
        "status": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Transaction status",
            example=RebalanceTransactionStates.SKIPPED.value,
            enum=[
                RebalanceTransactionStates.MANUALLY_COMPLETED.value,
                RebalanceTransactionStates.SKIPPED.value
            ],
            nullable=True
        )
    }
)


close_rebalance_request_schema_dict = openapi.Schema(
    title="Close Rebalance",
    type=openapi.TYPE_OBJECT,
    properties={
        "rebalance_id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Rebalance identifier to close",
            example=123
        )
    },
    required=["rebalance_id"],
)


manual_complete_latest_rebalance_request_schema_dict = openapi.Schema(
    title="Manual Complete Latest Portfolio Rebalance Transaction",
    type=openapi.TYPE_OBJECT,
    required=["user_portfolio_id"],
    properties={
        "user_portfolio_id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="User portfolio identifier",
            example=123,
        ),
    },
)

manual_complete_latest_rebalance_response_schema_dict = {
    "200": openapi.Response(
        description="Latest transaction marked as manually completed",
        examples={
            "application/json": {
                "data": {
                    "portfolio_rebalance_transaction_id": 456,
                    "status": RebalanceTransactionStates.MANUALLY_COMPLETED.value,
                }
            }
        },
    ),
    "404": openapi.Response(
        description="No eligible transaction found",
        examples={
            "application/json": {
                "detail": "No eligible transaction found for manual completion."
            }
        },
    ),
}