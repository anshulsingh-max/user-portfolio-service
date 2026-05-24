"""
    Holdings APIs
"""
import logging

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.holdings.apis.schemas.holdings import holdings_response_schema_dict, all_users_holdings_response_schema_dict
from apps.holdings.serializers.holdings import HoldingSerializer
from apps.holdings.serializers.positions import PositionsReadSerializer
from apps.holdings.services.holdings import get_user_portfolio_holdings, get_user_portfolio_holdings_optimized
from apps.portfolio.constants import UserPortfolioStatus, BasketStates
from apps.portfolio.services.user_portfolio import get_user_portfolios

from apps.holdings.apis.validators.holdings import BrokerUsersHoldingsQueryParamsValidator
from apps.holdings.serializers.holdings import AllUsersHoldingSerializer
from collections import defaultdict
from apps.holdings.models import Holding, Position
from apps.holdings.apis.validators.bulk_holdings import BulkHoldingsParamsValidator

logger = logging.getLogger(__name__)


class Holdings(GenericAPIView):
    """
        Class for Holdings API
    """
    @swagger_auto_schema(operation_description='GET User Portfolio Holdings',
                         responses=holdings_response_schema_dict)
    def get(self, request, user_portfolio_id):
        """
            Get holdings of a user portfolio
            :return: Response object
        """
        logger.info("In get user portfolio holdings API")

        holdings_queryset = get_user_portfolio_holdings([user_portfolio_id])
        ser = HoldingSerializer(instance=holdings_queryset, many=True)
        return Response(ser.data)


class BulkHoldings(GenericAPIView):
    """Bulk holdings endpoint.

    POST body: {"userPortfolioIds": [1, 2, ...], "fromCache": bool}
    Response: {"holdings": {"<user_portfolio_id>": [ ...holding objects... ], ... }}
    """

    @swagger_auto_schema(
        operation_description='POST Bulk User Portfolio Holdings',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'userPortfolioIds': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description='List of user portfolio IDs',
                ),
                'fromCache': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Use cached holdings if available'),
            },
            required=['userPortfolioIds'],
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'holdings': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        additional_properties=openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_OBJECT),
                        ),
                    )
                },
            )
        },
    )
    def post(self, request):
        logger.info("In BulkHoldings API")
        validator = BulkHoldingsParamsValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        validated = validator.validated_data
        user_portfolio_ids = validated['user_portfolio_ids']

        # Currently we ignore fromCache and always hit DB, reusing existing logic.
        holdings_qs = get_user_portfolio_holdings(user_portfolio_ids)
        ser = HoldingSerializer(instance=holdings_qs, many=True)

        grouped = defaultdict(list)
        for holding in ser.data:
            # holding['user_portfolio'] is the FK id
            grouped[str(holding['user_portfolio'])].append(holding)

        return Response({'holdings': grouped})


class UserHoldings(GenericAPIView):
    """
        Class for UserHoldings API
    """
    @swagger_auto_schema(
        operation_description='GET User Holdings for all portfolios',
        manual_parameters=[
            openapi.Parameter(
                'broker', openapi.IN_QUERY, description='Broker name', type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'product_type', openapi.IN_QUERY, description='Product type', type=openapi.TYPE_STRING, required=False
            ),
        ],
        responses=holdings_response_schema_dict,
    )
    def get(self, request, user_id):
        """
            Get holdings of a user for all of its portfolios
            :return: Response object
        """
        logger.info("In get user holdings API")

        broker = request.GET['broker']
        product_type = request.GET.get('product_type')
        # user_portfolio_queryset = get_user_portfolios(
        #     user_id,
        #     None,
        #     broker,
        #     status=UserPortfolioStatus.ACTIVE.value,
        #     product_type=product_type,
        # )
        # user_portfolio_ids = user_portfolio_queryset.values_list('id', flat=True)
        # holdings_queryset = get_user_portfolio_holdings(user_portfolio_ids)
        holdings_queryset = get_user_portfolio_holdings_optimized(user_id, broker, product_type)
        ser = HoldingSerializer(instance=holdings_queryset, many=True)
        return Response(ser.data)


class BrokerUsersHoldings(GenericAPIView):

    @swagger_auto_schema(operation_description='GET All Users Holdings',
                         responses=all_users_holdings_response_schema_dict)
    def get(self, request, broker_name):
        try:
            validator = BrokerUsersHoldingsQueryParamsValidator(data={'broker': broker_name})
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            broker_name = validated_data['broker']
            holdings_queryset = Position.objects.select_related('basket').filter(quantity__gt=0, basket__broker=broker_name, basket__current_state=BasketStates.MONITORING.value)
            ser = PositionsReadSerializer(instance=holdings_queryset, many=True)
            holdings = ser.data
            grouped_holdings = defaultdict(list)
            for holding in holdings:
                grouped_holdings[holding['user_id']].append({'symbol': holding['symbol'], 'quantity': holding['quantity']})
            return Response(dict(grouped_holdings))
        except Exception as exc:
            logger.exception(exc)
            raise exc
