"""
Schemas for transaction requests and responses APIs
"""

from drf_yasg import openapi

from apps.holdings.constants import TransactionSide

init_transaction_request_schema_dict = openapi.Schema(
    title="Initialize Transaction",
    type=openapi.TYPE_OBJECT,
    properties={
        'user_portfolio': openapi.Schema(type=openapi.TYPE_NUMBER, description=('User Portfolio ID'), example=100),
        'transaction_side': openapi.Schema(type=openapi.TYPE_STRING, description=('Addition or Withdrawal'),
                                           example=TransactionSide.CREDIT.value, enum=[TransactionSide.CREDIT.value,
                                           TransactionSide.DEBIT.value]),
        'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description=('Amount to allocate'), example=10000)
    }
)


transaction_response_schema_dict = {
    "200": openapi.Response(
        description="Transaction Response",
        examples={
            "application/json":
                {
              "data": {
                "transaction_id": 7
              },
              "error": False,
              "payload": {
                "user_portfolio": 1,
                "transaction_side": "credit",
                "amount": 10000
              }
            }
        }
    )
}
