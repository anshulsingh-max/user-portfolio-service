"""
    Transaction APIs
"""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.portfolio.apis.schemas.rebalance_transaction import rebalance_transaction_request_schema_dict, \
    user_portfolio_rebalance_transaction_response_schema_dict, get_portfolio_rebalance_transaction_schema_dict, \
    update_portfolio_transaction_schema_dict, update_portfolio_transaction_request_schema_dict
from apps.portfolio.apis.validators.rebalance_transaction import RebalanceTransactionParamsValidator, \
    UpdatePortfolioTransactionParamsValidator
from apps.portfolio.models import PortfolioRebalanceTransaction
from apps.portfolio.serializers.portfolio_rebalance_transaction import PortfolioRebalanceTransactionSerializer, \
    ReadPortfolioRebalanceTransactionSerializer
from apps.portfolio.services.rebalance_transaction import get_type_of_rebalance_transaction, \
    is_rebalance_transaction_active, get_user_portfolio_rebalance_transaction

logger = logging.getLogger(__name__)


class RebalanceTransaction(GenericAPIView):
    """
        Class for get brokerages APIs
    """
    @swagger_auto_schema(request_body=rebalance_transaction_request_schema_dict,
                         responses=user_portfolio_rebalance_transaction_response_schema_dict)
    def post(self, request):
        """
            Add Rebalance transaction record
            :return: Response object
        """
        logger.info("In RebalanceTransaction API")
        validator = RebalanceTransactionParamsValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        validated_data = validator.validated_data
        validated_data['type'] = get_type_of_rebalance_transaction(validated_data.get('portfolio_rebalance'))
        logger.info(f"{validated_data = }")

        ser = PortfolioRebalanceTransactionSerializer(data=validated_data)
        if (ser.is_valid(raise_exception=True) and not
                is_rebalance_transaction_active(validated_data['portfolio_rebalance'], raise_exception=True)):
            instance = ser.save()
            ret_ser = ReadPortfolioRebalanceTransactionSerializer(instance=instance)
            return Response(ret_ser.data)


class GetRebalanceTransaction(GenericAPIView):
    @swagger_auto_schema(operation_description='GET User Portfolios Rebalance Transaction',
                         responses=get_portfolio_rebalance_transaction_schema_dict)
    def get(self, request, portfolio_rebalance_transaction_id):
        """
            Rebalance Transactions
        """
        try:
            logger.info(f"In user portfolio rebalance transaction get api")
            instance = get_user_portfolio_rebalance_transaction(portfolio_rebalance_transaction_id)
            logger.info(f"{instance = }")
            read_ser = ReadPortfolioRebalanceTransactionSerializer(instance=instance)
            return Response(read_ser.data)
        except Exception as exc:
            logger.info(f"exception occured while retrieving user portfolio rebalance transaction")
            logger.exception(exc)
            raise exc


class UpdatePortfolioTransaction(GenericAPIView):

    @swagger_auto_schema(operation_description='Update Portfolios Rebalance Transaction',
                         responses=update_portfolio_transaction_schema_dict,
                         request_body=update_portfolio_transaction_request_schema_dict)
    def put(self, request, portfolio_rebalance_transaction_id):
        """
            Updates the given fields for portfolio rebalance transaction.
        """
        try:
            logger.info(f"In - UpdatePortfolioTransaction API")
            validator = UpdatePortfolioTransactionParamsValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            logger.info(f"{portfolio_rebalance_transaction_id =}, {validated_data =}")
            data = PortfolioRebalanceTransaction.objects.filter(id=portfolio_rebalance_transaction_id,
                                                                type=validated_data.get("type")).update(**validated_data)
            return Response(data)
        except Exception as exc:
            logger.info(f"exception occurred while updating portfolio rebalance transaction")
            logger.exception(exc)
            raise exc
