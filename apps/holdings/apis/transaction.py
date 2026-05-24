"""
    Transaction APIs
"""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.holdings.apis.schemas.transaction import init_transaction_request_schema_dict, \
    transaction_response_schema_dict
from apps.holdings.apis.validators.holdings import TransactionParamsValidator
from apps.holdings.constants import TransactionTypes
from apps.holdings.serializers.transaction import TransactionSerializer
from apps.exceptions.user_portfolio import UserPortfolioNotFound

logger = logging.getLogger(__name__)


class Transaction(GenericAPIView):
    """
        Class for get brokerages APIs
    """
    @swagger_auto_schema(request_body=init_transaction_request_schema_dict, responses=transaction_response_schema_dict)
    def post(self, request):
        """
            Add transaction record
            :return: Response object
        """
        try:
            logger.info("In save transaction API")
            validator = TransactionParamsValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            validated_data['type'] = TransactionTypes.CASH_REMOVAL.value \
                if validated_data.get("type") == TransactionTypes.CASH_REMOVAL.value else TransactionTypes.CASH_INGESTED.value
            logger.info(f"{validated_data = }")

            ser = TransactionSerializer(data=validated_data)
            if ser.is_valid(raise_exception=True):
                instance = ser.save()
                return Response({"transaction_id": instance.id})
        except Exception as exc:
            logger.exception(exc)
            raise UserPortfolioNotFound(message="fwr")
