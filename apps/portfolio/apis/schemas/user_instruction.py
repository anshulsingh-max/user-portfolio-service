"""
    Schemas for User Instruction Request and Response API
"""

from drf_yasg import openapi

from apps.portfolio.constants import Side, OrderStatus

user_instruction_request_schema_dict = [
    openapi.Parameter(name='id', in_=openapi.IN_PATH, description='ID of the User Instruction to retrieve', example=1,
                      type=openapi.TYPE_INTEGER,required=True)
]

user_instruction_response_schema_dict = {
    "200": openapi.Response(
        description='Retrieve User Instruction by ID',
        examples={
            "application/json":{
                "data":{

                },
                "error":False,
                "payload": {
                    "id": 1
                }
            }
        }
    )
}

update_trade_details_request_schema_dict = openapi.Schema(
    title="Update trade details",
    type=openapi.TYPE_OBJECT,
    properties={
                  "trade_placement_id": openapi.Schema(type=openapi.TYPE_INTEGER, description='Trade Placement ID',
                                                       example=1),
                  "order_tag": openapi.Schema(type=openapi.TYPE_STRING, description=('Specific order tag provided by '
                                                                                     'the user portfolio service'),
                                         example="hvrdybtfunygimuhio"),
                  "symbol": openapi.Schema(type=openapi.TYPE_STRING, description='Symbol of stock', example="HDFCBANK"),
                  "quantity": openapi.Schema(type=openapi.TYPE_NUMBER, description='Quantity to trade', example=1),
                  "filled_quantity": openapi.Schema(type=openapi.TYPE_NUMBER, description='Quantity Filled', example=1),
                  "side": openapi.Schema(type=openapi.TYPE_STRING, description='Side of trade', example=Side.BUY.value,
                                         enum=[Side.BUY.value, Side.SELL.value]),
                  "value": openapi.Schema(type=openapi.TYPE_NUMBER, description="Value of total trade", example=1000),
                  "status": openapi.Schema(type=openapi.TYPE_STRING, description="Status of trade",
                                           example=OrderStatus.FILLED.value,
                                           enum=[OrderStatus.FILLED.value, OrderStatus.WAITING.value,
                                                 OrderStatus.PARTIAL.value, OrderStatus.CANCEL.value]),
                  "price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Price of the Stock", example=150.40),
    }
)
