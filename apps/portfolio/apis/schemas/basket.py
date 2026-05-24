from drf_yasg import openapi

from apps.portfolio.constants import BasketStates, BasketTypes, ProductTypes

"""
swagger_schemas.py

This module contains the Swagger schema definitions for the Create User Portfolio API. 
It defines the request and response structures used in the API documentation, 
facilitating the integration and understanding of the API's functionality by developers.
"""

create_basket_swagger_schema = openapi.Schema(
    title="Create User Basket",
    type=openapi.TYPE_OBJECT,
    properties={
        "user_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Basket ID of the User',
            example='USR121'
        ),
        "broker": openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Basket is connected to what broker',
            example='hdfc'
        ),
        "model_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Model ID from content',
            example='SUPERSTAR'
        ),
        "basket_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Type of Basket',
            example='normal',
            enum=[BasketTypes.NORMAL.value, BasketTypes.CO.value]
        ),
        "product_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Type of product for basket',
            example='mtf',
            enum=[ProductTypes.MTF.value, ProductTypes.INTRADAY.value]
        ),
        "payment_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Payment ID',
            example='pay_werdfgvbntyghjk'
        ),
        "recommendation_id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Recommendation ID from catalogue',
            example=1
        ),
        "user_allocation": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description='Allocations selected by the user',
            example=[{
                'symbol': 'TCS',
                'side': 'buy',
                'quantity': 1,
                'leverage': 0.05
            }]
        ),
        "cash_ingested": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description='Cash invested',
            example=1000
        ),
        "profit_target_1": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description='Profit target 1',
            example=3
        ),
        "profit_target_2": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description='Profit target 2',
            example=6
        )
    }
)

create_basket_swagger_response = {
    "201": openapi.Response(
        description="Basket Response",
        examples={
            "application/json": {
                "data": {
                    "user_id": "USR121",
                    "current_state": "waiting",
                    "model_id": "SUPERSTAR",
                    "basket_type": "normal",
                    "product_type": "mtf",
                    "payment_id": "pay_werdfgvbntyghjk",
                    "recommendation_id": 1,
                    "user_allocation": {},
                    "cash_ingested": None,
                    "amount": None,
                    "profit_target": None,
                    "profit_target_value": None
                },
                "error": None,
                "payload": {
                    "user_id": "USR121",
                    "model_id": "SUPERSTAR",
                    "payment_id": "pay_werdfgvbntyghjk",
                    "recommendation_id": 1
                }
            }
        }
    ),
    "401": openapi.Response(
        description="Unauthorized"
    )
}

get_basket_request_schema = [
    openapi.Parameter(name='user_id', in_=openapi.IN_QUERY, description='User ID',
                      example='USR121', type=openapi.TYPE_STRING),
    openapi.Parameter(name='current_state', in_=openapi.IN_QUERY, description='current state of the portfolio',
                      example=BasketStates.WAITING.value, enum=[BasketStates.UNINVESTED.value,
                                                                BasketStates.WAITING.value,
                                                                BasketStates.MONITORING.value,
                                                                BasketStates.COMPLETE.value],
                      type=openapi.TYPE_STRING)
]

get_basket_response_schema = {
    "200": openapi.Response(
        description="Retrieving list of User Baskets",
        examples={
            "application/json": {
                "data": [
                    {
                        "user_id": "USR121",
                        "current_state": "waiting",
                        "model_id": "SUPERSTAR",
                        "payment_id": "pay_werdfgvbntyghjk",
                        "recommendation_id": 1,
                        "user_allocation": {},
                        "cash_ingested": None,
                        "amount": None,
                        "profit_target": None,
                        "profit_target_value": None
                    },
                    {
                        "user_id": "USR121",
                        "current_state": "waiting",
                        "model_id": "SUPERSTARTWO",
                        "payment_id": "pay_werdfgvbntyghjk",
                        "recommendation_id": 1,
                        "user_allocation": {},
                        "cash_ingested": None,
                        "amount": None,
                        "profit_target": None,
                        "profit_target_value": None
                    },
                    {
                        "user_id": "USR121",
                        "current_state": "waiting",
                        "model_id": "SUPERSTARTHREE",
                        "payment_id": "pay_werdfgvbntyghjk",
                        "recommendation_id": 1,
                        "user_allocation": {},
                        "cash_ingested": None,
                        "amount": None,
                        "profit_target": None,
                        "profit_target_value": None
                    }
                ],
                "error": False,
                "payload": {
                    "user_id": "USR121",
                    "current_state": "waiting"
                }
            }
        }
    )
}

update_basket_request_schema = openapi.Schema(
    title="Create User Portfolio",
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Basket ID ',
            example=1
        ),
        "user_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Basket ID of the User',
            example='USR121'
        ),
        "model_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Model ID from content',
            example='SUPERSTAR'
        ),
        "payment_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Payment ID',
            example='pay_werdfgvbntyghjk'
        ),
        "recommendation_id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Recommendation ID from catalogue',
            example=1
        ),
        "user_allocation": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description='Allocations selected by the user',
            example=[{
                'symbol': 'TCS',
                'side': 'buy',
                'quantity': 1,
                'leverage': 0.05
            }]
        ),
        "cash_ingested": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description='Cash invested',
            example=1000
        ),
        "amount": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description='Actual amount invested',
            example=9999.99
        ),
        "end_amount": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description='Actual amount invested',
            example=9999.99
        ),
        "profit_target": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description='Profit target',
            example=0.03
        ),
        "profit_target_value": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description='Profit target value calculated',
            example=100.11
        ),
    }
)

update_basket_response_schema = {
    "201": openapi.Response(
        description="Update Basket Response",
        examples={
            "application/json": {
                "data": {
                    "user_id": "USR121",
                    "current_state": "waiting",
                    "model_id": "SUPERSTAR",
                    "payment_id": "pay_werdfgvbntyghjk",
                    "recommendation_id": 1,
                    "user_allocation": [
                        {
                            "side": "buy",
                            "symbol": "TCS",
                            "quantity": 1
                        }
                    ],
                    "cash_ingested": 100,
                    "amount": 98,
                    "profit_target": 0.03,
                    "profit_target_value": 100.9
                },
                "error": None,
                "payload": []
            }
        }
    ),
    "401": openapi.Response(
        description="Unauthorized"
    )
}

get_basket_details_schema = openapi.Schema(
    title="Get Basket Details",
    type=openapi.TYPE_OBJECT,
    properties={
        "basket_id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Basket ID ',
            example=1
        ),
        "recommendation_id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Recommendation ID',
            example=1
        )
    }
)