"""
    Transaction APIs
"""
import logging
import datetime

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.holdings.services.transaction import revert_cash_transaction
from apps.portfolio.apis.schemas.user_portfolio_rebalance import user_portfolio_rebalance_request_schema_dict, \
    user_portfolio_rebalance_response_schema_dict, get_user_portfolio_rebalance_request_schema_dict, \
    get_user_rebalance_orders_request_schema_dict, get_user_rebalance_response_schema_dict, \
    update_user_portfolio_rebalance_request_schema_dict, manually_complete_query_params, \
    close_rebalance_request_schema_dict, manual_complete_latest_rebalance_request_schema_dict, \
    manual_complete_latest_rebalance_response_schema_dict
from apps.portfolio.apis.validators.user_portfolio_rebalance import UserPortfolioRebalanceParamsValidator, \
    GetUserPortfolioRebalanceParamsValidator, GetRebalanceOrdersParamsValidator, \
    UpdateUserPortfolioRebalanceParamsValidator, ManuallyCompleteRebalanceParamsValidation, \
    CloseRebalanceParamsValidator, ManualCompleteLatestRebalanceTransactionValidator
from apps.portfolio.constants import States, RebalanceTransactionStates
from apps.portfolio.models import UserPortfolioRebalance, PortfolioRebalanceTransaction
from apps.portfolio.serializers.user_portfolio_rebalance import UserPortfolioRebalanceSerializer, \
    ReadUserPortfolioRebalanceSerializer
from apps.portfolio.services.user_portfolio_rebalance import is_rebalance_active, get_portfolio_rebalance, \
    get_latest_user_instructions_of_rebalance, update_user_portfolio_rebalance, close_rebalance, \
    manually_complete_latest_transaction
from apps.portfolio.apis.validators.bulk_rebalance import BulkRebalanceParamsValidator
from apps.portfolio.services.bulk_rebalance import get_user_portfolios_rebalances
from multitenant.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class AddUserPortfolioRebalance(GenericAPIView):
    """
        Class for User Portfolio Rebalance
    """
    @swagger_auto_schema(request_body=user_portfolio_rebalance_request_schema_dict,
                         responses=user_portfolio_rebalance_response_schema_dict)
    def post(self, request):
        """
            Add User Portfolio Rebalance record
            :return: Response object
        """
        logger.info("In UserPortfolioRebalance")
        validator = UserPortfolioRebalanceParamsValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        validated_data = validator.validated_data
        validated_data['states'] = States.REBALANCE_MAPPING.value[validated_data['type']]
        tenant_id=get_current_tenant()
        logger.info(f"In UserPortfolioRebalance {tenant_id = }")

        logger.info(f"{validated_data = }")
        ser = UserPortfolioRebalanceSerializer(data=validated_data)
        if ser.is_valid(raise_exception=True) and not is_rebalance_active(validated_data['user_portfolio'],
                                                                          raise_exception=True):
            instance = ser.save()
            return Response({"user_portfolio_rebalance_id": instance.id})


class GetUserPortfolioRebalance(GenericAPIView):
    """
        Class for get User Portfolio Rebalance
    """
    @swagger_auto_schema(manual_parameters=get_user_portfolio_rebalance_request_schema_dict,
                         responses=user_portfolio_rebalance_response_schema_dict)
    def get(self, request, user_portfolio_id):
        """
            Get User Portfolio Rebalance record
            :return: Response object
        """
        logger.info("In GetUserPortfolioRebalance")
        validator = GetUserPortfolioRebalanceParamsValidator(data=request.GET)
        validator.is_valid(raise_exception=True)
        validated_data = validator.validated_data
        validated_data['user_portfolio_id'] = user_portfolio_id
        logger.info(f"{validated_data = }")

        user_portfolio_rebalance_queryset = get_portfolio_rebalance(user_portfolio_id, validated_data['current_state'])
        ser = ReadUserPortfolioRebalanceSerializer(instance=user_portfolio_rebalance_queryset, many=True)
        return Response(ser.data)


class BulkUserPortfolioRebalance(GenericAPIView):
    """Bulk user-portfolio rebalances endpoint.

    POST body: {"userPortfolioIds": [...], "currentState": "complete,pending", "fromCache": bool}
    Response: {"rebalances": {"<user_portfolio_id>": [ ...rebalance objects... ], ... }}
    """

    @swagger_auto_schema(operation_description='POST Bulk User Portfolio Rebalances')
    def post(self, request):
        logger.info("In BulkUserPortfolioRebalance API")
        validator = BulkRebalanceParamsValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        validated = validator.validated_data

        user_portfolio_ids = validated['userPortfolioIds']
        current_states = validated.get('current_states')
        from_cache = validated.get('fromCache', False)

        logger.info(
            "BulkUserPortfolioRebalance request: ids=%d, fromCache=%s, states=%s",
            len(user_portfolio_ids),
            from_cache,
            current_states,
        )

        # Currently we ignore fromCache and always hit DB via bulk service.
        try:
            grouped = get_user_portfolios_rebalances(user_portfolio_ids, current_states)
        except Exception:
            logger.exception(
                "Failed to fetch bulk rebalances for portfolio_ids=%s, states=%s", user_portfolio_ids, current_states
            )
            # Let DRF's default exception handler convert this to a 500 with a generic error.
            raise

        return Response({'rebalances': grouped})


class UpdateDate(GenericAPIView):
    """
        Class for Updates Date of created to yesterday
    """
    def put(self, request, user_portfolio_rebalance_id):
        """
            Add User Portfolio Rebalance record
            This is a very use case specific API so not exposing it to swagger but can be found in postman
            user_portfolio_rebalance_id:
            :return: Response object
        """
        from apps.portfolio.models import UserPortfolioRebalance
        logger.info(f"In UpdateDate {user_portfolio_rebalance_id = }")
        upr_obj = UserPortfolioRebalance.objects.get(id=user_portfolio_rebalance_id)
        upr_obj.created = upr_obj.created - datetime.timedelta(days=1)
        upr_obj.save()
        return Response({"user_portfolio_rebalance_id": upr_obj.id, "date_updated": True})


class GetRebalanceOrders(GenericAPIView):
    """
        Class for Get Rebalance Orders
    """
    @swagger_auto_schema(manual_parameters=get_user_rebalance_orders_request_schema_dict,
                         responses=get_user_rebalance_response_schema_dict)
    def get(self, request):
        """
            Get User Portfolio Rebalance orders
            It will take input as type (initial,t0,t1) and user_portfolio_rebalance_id
            :return: Orders placed in the specific type category
        """
        logger.info("In GetRebalanceOrders")
        validator = GetRebalanceOrdersParamsValidator(data=request.GET)
        validator.is_valid(raise_exception=True)
        validated_data = validator.validated_data
        orders = get_latest_user_instructions_of_rebalance(validated_data['user_portfolio_rebalance_id'],
                                                           [validated_data['type']])
        user_portfolio_rebalance_obj = UserPortfolioRebalance.objects.get(id=validated_data['user_portfolio_rebalance_id'])
        user_portfolio_obj = user_portfolio_rebalance_obj.user_portfolio
        get_derived_values_method = getattr(user_portfolio_rebalance_obj, "get_derived_values")
        derived_values = get_derived_values_method([validated_data['type']])
        transaction_value = getattr(user_portfolio_rebalance_obj, f"{validated_data['type']}_transaction_value")
        remaining_value = getattr(user_portfolio_rebalance_obj, f"{validated_data['type']}_remaining_value")
        return_dict = {
            'orders': orders,
            'buy_value': derived_values.get('buy_value'),
            'sell_value': derived_values.get('sell_value'),
            'invested_amount': user_portfolio_obj.invested_amount,
            'remaining_amount': remaining_value,
            'transaction_value': transaction_value,
            'user_portfolio_id': user_portfolio_obj.id,
            'product_type':user_portfolio_obj.product_type

        }
        return Response(return_dict)


class UpdateUserPortfolioRebalance(GenericAPIView):
    """
        Class for update user portfolio rebalance
    """
    @swagger_auto_schema(request_body=update_user_portfolio_rebalance_request_schema_dict)
    def put(self, request, user_portfolio_rebalance_id):
        """
            Update the details of user portfolio rebalance
            :return: Response object
        """
        logger.info("In UpdateUserPortfolioRebalance API")
        validator = UpdateUserPortfolioRebalanceParamsValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        validated_data = validator.validated_data
        logger.info(f"{validated_data = }")
        update_user_portfolio_rebalance(user_portfolio_rebalance_id, validated_data)
        return Response({"data": "Details Updated"})


class ManualCompleteRebalanceTransaction(GenericAPIView):
    """
        Class for update portfolio rebalance state to manually completed.
    """
    @swagger_auto_schema(request_body=manually_complete_query_params)
    def put(self, request, portfolio_rebalance_transaction_id):
        """
            Update the current state portfolio rebalance
            :return: Response object
        """
        logger.info("In ManualCompleteRebalanceTransaction API")
        validator = ManuallyCompleteRebalanceParamsValidation(data=request.data)
        validator.is_valid(raise_exception=True)
        validated_data = validator.validated_data
        logger.info(f"{validated_data = }")
        data_obj = PortfolioRebalanceTransaction.objects.get(id=portfolio_rebalance_transaction_id)
        data_obj.current_state = validated_data.get('status')
        data_obj.save()
        revert_cash_transaction(data_obj)
        return Response({"data": "Details Updated"})


class ManualCompleteLatestRebalanceTransaction(GenericAPIView):
    """Mark the latest eligible portfolio rebalance transaction as manually completed."""

    @swagger_auto_schema(
        request_body=manual_complete_latest_rebalance_request_schema_dict,
        responses=manual_complete_latest_rebalance_response_schema_dict,
    )
    def post(self, request):
        logger.info("In ManualCompleteLatestRebalanceTransaction API")
        validator = ManualCompleteLatestRebalanceTransactionValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        user_portfolio_id = validator.validated_data["user_portfolio_id"]
        transaction = manually_complete_latest_transaction(user_portfolio_id)
        if not transaction:
            logger.info(
                f"Manual completion not performed - no eligible transaction for user_portfolio_id={user_portfolio_id}")
            return Response({"message": "No eligible partially completed transaction found."})

        response_payload = {
            "message": "Manual completion successful.",
            "portfolio_rebalance_transaction_id": transaction.id,
            "user_portfolio_rebalance_id": transaction.portfolio_rebalance_id,
            "status": transaction.current_state,
        }
        logger.info(
            f"Manual completion successful for user_portfolio_id={user_portfolio_id}, transaction_id={transaction.id}"
        )
        return Response(response_payload)


class CloseRebalance(GenericAPIView):
    """Manually close a rebalance."""

    @swagger_auto_schema(request_body=close_rebalance_request_schema_dict)
    def post(self, request):
        logger.info("In CloseRebalance API")
        validator = CloseRebalanceParamsValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        rebalance_id = validator.validated_data.get("rebalance_id")
        result = close_rebalance(rebalance_id)

        return Response({"data": result})
