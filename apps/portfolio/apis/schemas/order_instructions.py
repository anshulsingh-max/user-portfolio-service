from drf_yasg import openapi

from apps.portfolio.constants import Side

create_order_instructions_schema = openapi.Schema(
    title="Create Order Instructions",
    type=openapi.TYPE_OBJECT,
    properties={
        "instructions": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description='List of instructions for orders',
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "order_id": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description='ID of the order to which the user instruction belongs',
                        example=120
                    ),
                    "symbol": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Trading Symbol',
                        example='RELIANCE'
                    ),
                    "quantity": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description='Quantity to trade.',
                        example=2
                    ),
                    "side": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Side for the trade',
                        example='sell',
                        enum=["buy", "sell"]
                    ),
                }
            )
        )
    }
)
