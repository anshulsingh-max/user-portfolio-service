"""
    Schemas for User Portfolio request and response APIs
"""
from drf_yasg import openapi
from apps.portfolio.constants import UserPortfolioStatus, InvestmentStatus

init_portfolio_request_schema_dict = openapi.Schema(
    title="Create User Portfolio",
    type=openapi.TYPE_OBJECT,
    properties={
        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description='User Portfolio ID', example='USR121'),
        "name": openapi.Schema(type=openapi.TYPE_STRING, description='Name of the User', example='Jay'),
        "portfolio_id": openapi.Schema(type=openapi.TYPE_STRING, description='Id of the Portfolio', example='AISLCT'),
        "status": openapi.Schema(type=openapi.TYPE_STRING, description='status of the portfolio',
                                 example=UserPortfolioStatus.ACTIVE.value,
                                 enum=[UserPortfolioStatus.ACTIVE.value, UserPortfolioStatus.INACTIVE.value]),
        "subscription_id": openapi.Schema(type=openapi.TYPE_STRING, description='Id of the Subscription',
                                          example='AI1287ad'),
        "proxy": openapi.Schema(type=openapi.TYPE_STRING, description='Proxy for the user. User/Dealer',
                                example='dealer'),
        "product_type": openapi.Schema(type=openapi.TYPE_STRING, description='Product type of the Portfolio',
                                       example='mtf', ),
        "strategy": openapi.Schema(type=openapi.TYPE_STRING,
                                   description="Strategy Type i.e rebalance/one_time",
                                   example='rebalance')
    }
)

portfolio_response_schema_dict = {
    "201": openapi.Response(
        description="User Portfolio Response",
        examples={
            "application/json": {
                "data": {
                    "id": 1
                },
                "error": False,
                "payload": {
                    "user_id": "USR12",
                    "name": "Jay Prakash",
                    "portfolio_id": "JPYQ",
                    "status": "active",
                    "subscription_id": "AI1287ad"
                }
            }
        }
    ),
    "401": openapi.Response(
        description="Unauthorized"
    )
}

portfolio_details_request_schema_dict = [
    openapi.Parameter(name='user_id', in_=openapi.IN_QUERY, description='User ID',
                      example='USR16897462096495242304', type=openapi.TYPE_STRING),
    openapi.Parameter(name='portfolio_id', in_=openapi.IN_QUERY, description='Portfolio Id',
                      example='EQTRKT', type=openapi.TYPE_STRING),
    openapi.Parameter(name='broker', in_=openapi.IN_QUERY, description='Broker',
                      example='lkp', type=openapi.TYPE_STRING),
    openapi.Parameter(name='status', in_=openapi.IN_QUERY, description='status of the portfolio',
                      example=UserPortfolioStatus.ACTIVE.value, enum=[UserPortfolioStatus.ACTIVE.value,
                                                                      UserPortfolioStatus.INACTIVE.value],
                      type=openapi.TYPE_STRING),
    openapi.Parameter(name='investment_status', in_=openapi.IN_QUERY, description='investment status of the portfolio',
                      example=InvestmentStatus.INVESTED.value, enum=[InvestmentStatus.INVESTED.value,
                                                                     InvestmentStatus.UNINVESTED.value],
                      required=False, type=openapi.TYPE_STRING),
    openapi.Parameter(name='subscription_id', in_=openapi.IN_QUERY, description='Subscription ID for the user',
                      example='sub_errtyufsfhghhfgxf', type=openapi.TYPE_STRING),
    openapi.Parameter(name='product_type', in_=openapi.IN_QUERY, description='Product type of the Portfolio',
                      example='cnc', type=openapi.TYPE_STRING),
    openapi.Parameter(name='strategy', in_=openapi.IN_QUERY, description='Strategy Type i.e rebalance/one_time',
                      example='one_time', type=openapi.TYPE_STRING)
]

portfolio_details_response_schema_dict = {
    "200": openapi.Response(
        description="Retrieving list of User Portfolios",
        examples={
            "application/json": {
                "data": {

                },
                "error": False,
                "payload": {
                    "user_id": "USR16897462096495242304",
                    "status": "active"
                }
            }
        }
    )
}

user_portfolio_request_schema_dict = [
    openapi.Parameter(name='id', in_=openapi.IN_PATH, description='ID of the user portfolio', example=1,
                      type=openapi.TYPE_INTEGER)
]

user_portfolio_response_schema_dict = {
    "200": openapi.Response(
        description="Retrieve User Portfolio by ID",
        examples={
            "application/json": {
                "data": {

                },
                "error": False,
                "payload": {
                    "id": 1
                }
            }
        }
    )
}

delete_user_portfolio_response_schema_dict = {
    "200": openapi.Response(
        description="Delete User Portfolio by ID",
        examples={
            "application/json": {
                "data": {
                    "message": "Deletion successful",
                    "deletion_details": []
                },
                "error": False,
                "payload": {
                    "id": 1
                }
            }
        }
    )
}

reset_user_portfolio_response_schema_dict = {
    "200": openapi.Response(
        description="Reset User Portfolio of User",
        examples={
            "application/json": {
                "data": {
                    "message": "User portfolio reset successful",
                },
                "error": False,
                "payload": {
                    "id": 1
                }
            }
        }
    )
}

user_portfolio_update_request_schema_dict = openapi.Schema(
    title="Update User Portfolio by ID",
    type=openapi.TYPE_OBJECT,
    properties={
        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description='User Portfolio ID', example='USR121'),
        "name": openapi.Schema(type=openapi.TYPE_STRING, description='Name of the User', example='Jay'),
        "portfolio_id": openapi.Schema(type=openapi.TYPE_STRING, description='Id of the Portfolio', example='AISLCT'),
        "status": openapi.Schema(type=openapi.TYPE_STRING, description='status of the portfolio',
                                 example=UserPortfolioStatus.ACTIVE.value,
                                 enum=[UserPortfolioStatus.ACTIVE.value, UserPortfolioStatus.INACTIVE.value])
    }
)

user_portfolio_reset_request_schema_dict = openapi.Schema(
    title="Reset User Portfolio of User",
    type=openapi.TYPE_OBJECT,
    properties={
        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description='User ID', example="123"),
    }
)

user_portfolio_update_subscription_id_request_schema_dict = openapi.Schema(
    title="Update User Portfolio by Subscription ID",
    type=openapi.TYPE_OBJECT,
    properties={
        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description='User Portfolio ID', example='8888888818'),
        "name": openapi.Schema(type=openapi.TYPE_STRING, description='Name of the User', example='Jay'),
        "portfolio_id": openapi.Schema(type=openapi.TYPE_STRING, description='Id of the Portfolio', example='AISLCT'),
        "status": openapi.Schema(type=openapi.TYPE_STRING, description='status of the portfolio',
                                 example=UserPortfolioStatus.ACTIVE.value,
                                 enum=[UserPortfolioStatus.ACTIVE.value, UserPortfolioStatus.INACTIVE.value])
    }
)

user_portfolio_update_path_request_schema_dict = [
    openapi.Parameter(
        name='id', in_=openapi.IN_PATH, description='ID of the Portfolio', example=1, type=openapi.TYPE_INTEGER)
]

user_portfolio_update_subscription_id_path_request_schema_dict = [
    openapi.Parameter(
        name='subscription_id', in_=openapi.IN_PATH, description='Subscription ID of the Portfolio',
        example='sub_NS0fZVaaOIdWqd',
        type=openapi.TYPE_STRING
    )
]

user_portfolio_update_response_schema_dict = {
    "200": openapi.Response(
        description="Update User Portfolio By ID",
        examples={
            "application/json": {
                "data": {
                    "id": 28,
                    "user_id": "9205448564",
                    "name": "Jay Prakash",
                    "portfolio_id": "INTELLECT",
                    "status": "inactive",
                    "subscription_id": "sub_NS0fZVQyOIdWqd",
                    "latest_rebalance": {},
                    "created": "2024-01-23T09:48:12.767337Z",
                    "modified": "2024-01-23T09:48:12.767383Z"
                },
                "error": False,
                "payload": {
                    "id": 1
                }
            }
        }
    )
}

user_portfolio_update_subscription_id_response_schema_dict = {
    "200": openapi.Response(
        description="Update User Portfolio By Subscription ID",
        examples={
            "application/json": {
                "data": {
                    "id": 28,
                    "user_id": "9205448564",
                    "name": "Jay Prakash",
                    "portfolio_id": "INTELLECT",
                    "status": "inactive",
                    "subscription_id": "sub_NS0fZVQyOIdWqd",
                    "latest_rebalance": {},
                    "created": "2024-01-23T09:48:12.767337Z",
                    "modified": "2024-01-23T09:48:12.767383Z"
                },
                "error": False,
                "payload": {
                    "id": 'sub_NS0fZVQyOIdWqd'
                }
            }
        }
    )
}

user_portfolio_positions_schema_dict = [
    openapi.Parameter(
        name='user_id', in_=openapi.IN_PATH, description='Get user portfolio holdings of a user', example='9205448564',
        type=openapi.TYPE_STRING
    )
]

user_portfolio_positions_response_schema_dict = {
    "200": openapi.Response(
        description="Get user portfolio holdings by user_id",
        examples={
            "application/json": {
                "data": {
                    "id": 28,
                    "user_id": "9205448564",
                    "name": "Jay Prakash",
                    "portfolio_id": "INTELLECT",
                    "status": "inactive",
                    "subscription_id": "sub_NS0fZVQyOIdWqd",
                    "latest_rebalance": {},
                    "created": "2024-01-23T09:48:12.767337Z",
                    "modified": "2024-01-23T09:48:12.767383Z"
                },
                "error": False,
                "payload": {
                    "user_id": '9205448564'
                }
            }
        }
    )
}


user_portfolio_summary_params = [
    openapi.Parameter(
        name='user_id', in_=openapi.IN_QUERY, description='Get user portfolio holdings of a user', example='9205448564',
        type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter(
        name='broker', in_=openapi.IN_QUERY, description='Associated broker name', example='demo',
        type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter(
        name='product_type', in_=openapi.IN_QUERY, description='Associated product type', example='mtf',
        type=openapi.TYPE_STRING, required=True
    )
]


user_portfolio_summary_response_schema_dict = {
    "200": openapi.Response(
        description="Get user portfolio summary",
        examples={
            "application/json": {
                "data": [
                    {
                        "user_portfolio_id": 738,
                        "user_id": "9115420432",
                        "portfolio_id": "INDAMT_7a2552",
                        "status": "active",
                        "is_invested": True
                    }
                ],
                "error": False,
                "payload": {
                    "user_id": '9205448564'
                }
            }
        }
    )
}
