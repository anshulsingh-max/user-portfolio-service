from drf_yasg import openapi
from apps.alerts.constants import PortfolioThresholdTypes, Status, ThresholdSource, PortfolioSides

"""
swagger_schemas.py

This module contains the Swagger schema definitions for the User Portfolio Threshold API.
It defines the request and response structures used in the API documentation,
facilitating integration and developer understanding.
"""


create_threshold_swagger_schema = openapi.Schema(
    title="Create User Portfolio Threshold",
    type=openapi.TYPE_OBJECT,
    properties={
        "portfolio_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Entity type this threshold applies to",
            example="user_portfolio"
        ),
        "portfolio_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Entity ID this threshold applies to",
            example="1"
        ),
        "side": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Side of the portfolio (LONG/SHORT)",
            example="long"
        ),
        "threshold_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Type of threshold rule",
            example="profit_target",
            enum=[PortfolioThresholdTypes.PROFIT_TARGET.value, PortfolioThresholdTypes.STOP_LOSS.value]
        ),
        "target_pct": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description="Percentage threshold (e.g., 0.1 for 10%)",
            example=0.1
        ),
        "target_value": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description="Absolute threshold value (e.g., ₹10000)",
            example=10000.00
        ),
        "status": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Status of the threshold rule",
            example="active",
            enum=[Status.ACTIVE.value, Status.INACTIVE.value]
        ),
        "source": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Origin of the rule (User/Admin/Dealer)",
            example="user",
            enum=[ThresholdSource.USER.value, ThresholdSource.ADMIN.value, ThresholdSource.DEALER.value]
        ),
        "source_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Origin ID of the rule (User ID/Admin ID/Dealer ID)",
            example="9999999999"
        ),
        "effective_from": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Optional expiry timestamp for the threshold"
        ),
    },
    required=["portfolio_type", "portfolio_id", "threshold_type", "status", "source"]
)


create_threshold_swagger_response = {
    "200": openapi.Response(
        description="User Portfolio Threshold Response",
        examples={
            "application/json": {
                "data": {
                    "id": 101,
                    "portfolio_type": "USER_PORTFOLIO",
                    "portfolio_id": "PORT123",
                    "side": "long",
                    "threshold_type": "profit_target",
                    "target_pct": 0.1,
                    "target_value": None,
                    "status": "active",
                    "source": "user",
                    "source_id": "9999999999",
                    "effective_from": "2025-08-21T10:30:00Z",
                    "effective_to": None,
                    "triggered_at": None,
                    "last_notification_sent_at": None,
                    "created": "2025-08-21T10:30:00Z",
                    "modified": "2025-08-21T10:30:00Z"
                },
                "error": None
            }
        }
    ),
    "401": openapi.Response(
        description="Unauthorized"
    )
}


get_user_portfolio_threshold_request_schema = [
    openapi.Parameter(
        name="portfolio_type",
        in_=openapi.IN_QUERY,
        description="Type of portfolio entity",
        example="user_portfolio",
        type=openapi.TYPE_STRING,
        required=True
    ),
    openapi.Parameter(
        name="portfolio_id",
        in_=openapi.IN_QUERY,
        description="ID of the portfolio entity",
        example="7",
        type=openapi.TYPE_STRING,
        required=True
    ),
    openapi.Parameter(
        name="side",
        in_=openapi.IN_QUERY,
        description="Position side",
        example=PortfolioSides.LONG.value,
        enum=[PortfolioSides.LONG.value, PortfolioSides.SHORT.value],
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        name="threshold_type",
        in_=openapi.IN_QUERY,
        description="Threshold type",
        example=PortfolioThresholdTypes.PROFIT_TARGET.value,
        enum=[choice.value for choice in PortfolioThresholdTypes],
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        name="status",
        in_=openapi.IN_QUERY,
        description="Threshold status",
        example=Status.ACTIVE.value,
        enum=[choice.value for choice in Status],
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        name="source_id",
        in_=openapi.IN_QUERY,
        description="Source ID (User ID/Admin ID/Dealer ID)",
        example="9999999999",
        type=openapi.TYPE_STRING
    ),
]


get_user_portfolio_threshold_response_schema = {
    "200": openapi.Response(
        description="Retrieve list of User Portfolio Thresholds",
        examples={
            "application/json": {
                "data": [
                    {
                        "id": 1,
                        "portfolio_type": "user_portfolio",
                        "portfolio_id": "7",
                        "side": "long",
                        "threshold_type": "profit_target",
                        "target_pct": "0.02",
                        "target_value": "10000.00",
                        "status": "active",
                        "source": "user",
                        "source_id": "9999999999",
                        "effective_from": "2025-08-22T06:14:46.343Z",
                        "created": "2025-08-22T06:14:46.343Z",
                        "modified": "2025-08-22T06:14:46.343Z"
                    },
                    {
                        "id": 2,
                        "portfolio_type": "user_portfolio",
                        "portfolio_id": "7",
                        "side": "long",
                        "threshold_type": "profit_target",
                        "target_pct": "0.05",
                        "target_value": "25000.00",
                        "status": "active",
                        "source": "user",
                        "source_id": "9999999999",
                        "effective_from": "2025-08-22T06:15:46.343Z",
                        "created": "2025-08-22T06:15:46.343Z",
                        "modified": "2025-08-22T06:15:46.343Z"
                    }
                ],
                "error": False,
                "payload": {
                    "portfolio_type": "user_portfolio",
                    "portfolio_id": "7",
                    "side": "long",
                    "threshold_type": "profit_target",
                    "status": "active",
                    "source_id": "9999999999"
                }
            }
        }
    )
}


update_threshold_request_schema = [
    openapi.Parameter(
        name="portfolio_type", in_=openapi.IN_QUERY, description="Portfolio type", required=True,
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        name="portfolio_id", in_=openapi.IN_QUERY, description="Portfolio ID", required=True,
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        name="side", in_=openapi.IN_QUERY, description="Position side (long/short)", required=False,
        type=openapi.TYPE_STRING, enum=[PortfolioSides.LONG.value, PortfolioSides.SHORT.value]
    ),
    openapi.Parameter(
        name="threshold_type", in_=openapi.IN_QUERY, description="Threshold type (profit_target/stop_loss)", required=False,
        type=openapi.TYPE_STRING, enum=[PortfolioThresholdTypes.PROFIT_TARGET.value, PortfolioThresholdTypes.STOP_LOSS.value]
    ),
]

update_threshold_request_body_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Basket ID ',
            example=1
        ),
        "target_pct": openapi.Schema(type=openapi.TYPE_NUMBER,
                                     description="New percentage threshold"),
        "status": openapi.Schema(type=openapi.TYPE_STRING,
                                 description="Threshold status",
                                 enum=[Status.ACTIVE.value,
                                       Status.INACTIVE.value]),
        "source": openapi.Schema(type=openapi.TYPE_STRING,
                                 description="Origin of the update",
                                 enum=[ThresholdSource.USER.value,
                                       ThresholdSource.ADMIN.value,
                                       ThresholdSource.DEALER.value]),
        "source_id": openapi.Schema(type=openapi.TYPE_STRING,
                                    description="ID of the user, admin, or dealer"),
    },
    required=[]
)


update_threshold_response_schema = {
    "200": openapi.Response(
        description="Updated UserPortfolioThreshold",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "portfolio_type": openapi.Schema(type=openapi.TYPE_STRING),
                "portfolio_id": openapi.Schema(type=openapi.TYPE_STRING),
                "side": openapi.Schema(type=openapi.TYPE_STRING),
                "threshold_type": openapi.Schema(type=openapi.TYPE_STRING),
                "target_pct": openapi.Schema(type=openapi.TYPE_NUMBER),
                "target_value": openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                "status": openapi.Schema(type=openapi.TYPE_STRING),
                "source": openapi.Schema(type=openapi.TYPE_STRING),
                "source_id": openapi.Schema(type=openapi.TYPE_STRING),
                "effective_from": openapi.Schema(type=openapi.FORMAT_DATETIME),
                "created": openapi.Schema(type=openapi.FORMAT_DATETIME),
                "modified": openapi.Schema(type=openapi.FORMAT_DATETIME),
            }
        )
    )
}