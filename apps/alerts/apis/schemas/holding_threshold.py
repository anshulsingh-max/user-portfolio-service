from drf_yasg import openapi

from apps.alerts.constants import PortfolioThresholdTypes, Status, ThresholdSource, PortfolioSides

"""
Swagger Schemas for Holding Threshold APIs
-----------------------------------------
Defines request/response schemas for HoldingThreshold endpoints to power
OpenAPI (Swagger) documentation via drf-yasg.
"""

# -------------------- Create --------------------
create_threshold_swagger_schema = openapi.Schema(
    title="Create Holding Threshold",
    type=openapi.TYPE_OBJECT,
    properties={
        "holding_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Entity type this threshold applies to (e.g., STOCK, ETF)",
            example="STOCK",
        ),
        "holding_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Entity ID this threshold applies to (e.g., ticker symbol)",
            example="AAPL",
        ),
        "side": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Position side (LONG/SHORT)",
            example=PortfolioSides.LONG.value,
            enum=[PortfolioSides.LONG.value, PortfolioSides.SHORT.value],
        ),
        "threshold_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Type of threshold rule",
            example=PortfolioThresholdTypes.PROFIT_TARGET.value,
            enum=[choice.value for choice in PortfolioThresholdTypes],
        ),
        "target_pct": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description="Percentage threshold (0.1 == 10%)",
            example=0.1,
        ),
        "target_value": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description="Absolute threshold value (e.g., 10000.00)",
            example=10000.00,
        ),
        "status": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Status of the threshold rule",
            example=Status.ACTIVE.value,
            enum=[choice.value for choice in Status],
        ),
        "source": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Origin of the rule (User/Admin/Dealer)",
            example=ThresholdSource.USER.value,
            enum=[choice.value for choice in ThresholdSource],
        ),
        "source_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Origin ID of the rule (user id/admin id/dealer id)",
            example="9999999999",
        ),
    },
    required=[
        "holding_type",
        "holding_id",
        "side",
        "threshold_type",
        "status",
        "source",
    ],
)

create_threshold_swagger_response = {
    "200": openapi.Response(
        description="Holding Threshold created",
    ),
    "401": openapi.Response(description="Unauthorized"),
}

# -------------------- Retrieve (GET) --------------------
get_holding_threshold_request_schema = [
    openapi.Parameter(
        name="holding_type",
        in_=openapi.IN_QUERY,
        description="Holding type",
        example="STOCK",
        type=openapi.TYPE_STRING,
        required=True,
    ),
    openapi.Parameter(
        name="holding_id",
        in_=openapi.IN_QUERY,
        description="Holding ID",
        example="AAPL",
        type=openapi.TYPE_STRING,
        required=False,
    ),
    openapi.Parameter(
        name="side",
        in_=openapi.IN_QUERY,
        description="Position side",
        type=openapi.TYPE_STRING,
        enum=[PortfolioSides.LONG.value, PortfolioSides.SHORT.value],
    ),
    openapi.Parameter(
        name="threshold_type",
        in_=openapi.IN_QUERY,
        description="Threshold type",
        type=openapi.TYPE_STRING,
        enum=[choice.value for choice in PortfolioThresholdTypes],
    ),
    openapi.Parameter(
        name="status",
        in_=openapi.IN_QUERY,
        description="Status",
        type=openapi.TYPE_STRING,
        enum=[choice.value for choice in Status],
    ),
    openapi.Parameter(
        name="source_id",
        in_=openapi.IN_QUERY,
        description="Filter by source id",
        type=openapi.TYPE_STRING,
    ),
]

get_holding_threshold_response_schema = {
    "200": openapi.Response(description="List of Holding Thresholds"),
}

# -------------------- Update (PUT) --------------------
update_threshold_request_body_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Threshold id"),
        "target_pct": openapi.Schema(type=openapi.TYPE_NUMBER, description="New percentage threshold"),
        "status": openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=[choice.value for choice in Status],
            description="Threshold status",
        ),
        "source": openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=[choice.value for choice in ThresholdSource],
            description="Origin of the update",
        ),
        "source_id": openapi.Schema(type=openapi.TYPE_STRING, description="ID of user/admin/dealer"),
    },
)

update_threshold_response_schema = {
    "200": openapi.Response(description="Updated Holding Threshold"),
}