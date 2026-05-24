"""
    API to create User Portfolio
"""

import logging
import time

from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.portfolio.apis.schemas.portfolio import init_portfolio_request_schema_dict, portfolio_response_schema_dict, \
    portfolio_details_request_schema_dict, portfolio_details_response_schema_dict, user_portfolio_request_schema_dict, \
    user_portfolio_response_schema_dict, user_portfolio_update_response_schema_dict, \
    user_portfolio_update_request_schema_dict, user_portfolio_update_path_request_schema_dict, \
    delete_user_portfolio_response_schema_dict, user_portfolio_update_subscription_id_request_schema_dict, \
    user_portfolio_update_subscription_id_path_request_schema_dict, \
    user_portfolio_update_subscription_id_response_schema_dict, reset_user_portfolio_response_schema_dict, \
    user_portfolio_reset_request_schema_dict, user_portfolio_positions_response_schema_dict, \
    user_portfolio_positions_schema_dict, user_portfolio_summary_params, user_portfolio_summary_response_schema_dict
from apps.portfolio.serializers.user_portfolio import ReadUserPortfolioSerializer, UserPortfolioPositionsSerializer, \
    ReadUserPortfolioSerializerJTE
from apps.portfolio.serializers.user_portfolio_no_serialize import ReadUserPortfolioNoSerializerJTE
from apps.portfolio.services.user_portfolio import create_user_portfolio, get_user_portfolios, get_user_portfolio, \
    update_user_portfolio_by_id, delete_user_portfolio, update_user_portfolio_by_subscription_id, \
    reset_user_portfolio_of_user, get_user_portfolio_positions_user, fetch_user_portfolio_summary, \
    get_user_portfoliosJTE
from apps.portfolio.apis.validators.user_portfolio import UserPortfolioParamsValidator, \
    UserPortfolioQueryParamsValidator, UserPortfolioReqParamsValidator, UserPortfolioUpdateValidator, \
    UserPortfolioUpdateBySubscriptionIdValidator, UserPortfolioPositionParamsValidator, \
    UserPortfolioSummaryParamsValidator
from apps.portfolio.services.user_portfolio_threshold import get_active_thresholds_for_user

logger = logging.getLogger(__name__)


class UserPortfolioJTE(GenericAPIView):
    """
        Class for easy fetch for business service optimization
    """

    @swagger_auto_schema(operation_description='GET User Portfolios',
                         manual_parameters=portfolio_details_request_schema_dict,
                         responses=portfolio_details_response_schema_dict)
    def get(self, request):
        """
            Retrieve User Portfolio
        """
        try:
            logger.info(f"in user portfolio get api")
            st=time.time()
            validator = UserPortfolioQueryParamsValidator(data=request.GET)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            logger.info(f"user portfolio get api {validated_data = }")
            thresholds = None
            user_id = validated_data.get('user_id')
            ets=time.time()
            logger.debug(f"user portfolio get api {user_id = } time taken for validation {ets-st}")
            if user_id is not None:
                et = time.time()
                thresholds = get_active_thresholds_for_user(user_id)
                logger.debug(f"got threshold in time {time.time()-et}s")
            st=time.time()
            user_portfolios_query_set = get_user_portfoliosJTE(**validated_data)
            user_portfolios_query_set = list(user_portfolios_query_set)
            ets=time.time()
            logger.debug(f"time taken to get user portfolios {ets-st}s")
            # read_ser = ReadUserPortfolioSerializerJTE(user_portfolios_query_set, many=True, context={"thresholds": thresholds})
            # read_ser=read_ser.data
            read_ser= ReadUserPortfolioNoSerializerJTE(user_portfolios_query_set,thresholds).data()
            logger.debug(f"time taken to serialize user portfolios {time.time()-ets}s")
            return Response(read_ser)
        except Exception as exc:
            logger.info(f"exception occured while retrieving user portfolio")
            logger.exception(exc)
            raise exc


class UserPortfolio(GenericAPIView):
    """
        Class for creating User Portfolio
    """

    @swagger_auto_schema(request_body=init_portfolio_request_schema_dict, responses=portfolio_response_schema_dict)
    def post(self, request):
        """
            Create User portfolio
        """
        try:
            logger.info(f"In user portfolio create api")
            validator = UserPortfolioParamsValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            logger.info(f"user portfolio { validated_data = }")
            user_portfolio_obj = create_user_portfolio(validated_data)
            # logger.info(f"{user_portfolio_obj = }")
            read_ser = ReadUserPortfolioSerializer(instance=user_portfolio_obj)
            return Response(read_ser.data)
        except Exception as exc:
            logger.info(f"exception occured while creating user portfolio")
            logger.exception(exc)
            raise exc

    @swagger_auto_schema(operation_description='GET User Portfolios',
                         manual_parameters=portfolio_details_request_schema_dict,
                         responses=portfolio_details_response_schema_dict)
    def get(self, request):
        """
            Retrieve User Portfolio
        """
        try:
            logger.info(f"in user portfolio get api")
            validator = UserPortfolioQueryParamsValidator(data=request.GET)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            logger.info(f"user portfolio get api {validated_data = }")
            thresholds = None
            user_id = validated_data.get('user_id')
            if user_id is not None:
                thresholds = get_active_thresholds_for_user(user_id)
            user_portfolios_query_set = get_user_portfolios(**validated_data)
            read_ser = ReadUserPortfolioSerializer(user_portfolios_query_set, many=True, context={"thresholds": thresholds})
            return Response(read_ser.data)
        except Exception as exc:
            logger.info(f"exception occured while retrieving user portfolio")
            logger.exception(exc)
            raise exc


class UserPortfolioById(GenericAPIView):
    """
        Retrieve User Portfolio by id
    """

    @swagger_auto_schema(operation_description='GET User Portfolio by ID',
                         manual_parameters=user_portfolio_request_schema_dict,
                         responses=user_portfolio_response_schema_dict)
    def get(self, request, id):
        try:
            logger.info(f"in user portfolio by id api ")
            user_portfolio_by_id_query_set = get_user_portfolio(id)
            logger.info(f"{user_portfolio_by_id_query_set = }")
            read_ser = ReadUserPortfolioSerializer(instance=user_portfolio_by_id_query_set)
            return Response(read_ser.data)
        except Exception as exc:
            logger.info(f"exception occured while retrieving user portfolio {id = }")
            logger.exception(exc)
            raise exc

    @swagger_auto_schema(request_body=user_portfolio_update_request_schema_dict,
                         manual_parameters=user_portfolio_update_path_request_schema_dict,
                         responses=user_portfolio_update_response_schema_dict)
    def put(self, request, id):
        try:
            logger.info(f"in user portfolio update by id api")
            request.data['id'] = id
            validator = UserPortfolioUpdateValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            logger.info(f"user portfolio update api {validated_data = }")
            updated_user_portfolio = update_user_portfolio_by_id(validated_data)
            logger.info(f"{id = } {updated_user_portfolio = }")
            read_ser = ReadUserPortfolioSerializer(updated_user_portfolio)
            return Response(read_ser.data)
        except Exception as exc:
            logger.info(f"exception occured while updating user portfolio {id = } in api")
            logger.exception(exc)
            raise exc

    @swagger_auto_schema(operation_description='DELETE User Portfolio by ID',
                         manual_parameters=user_portfolio_request_schema_dict,
                         responses=delete_user_portfolio_response_schema_dict)
    def delete(self, request, id):
        try:
            logger.info(f"In delete user portfolio by id api ")
            deletion_obj = delete_user_portfolio(id)
            logger.info(f"{deletion_obj = }")
            ret_dict = {
                "message": "Deletion successful",
                "deletion_details": deletion_obj
            }
            return Response(ret_dict)
        except Exception as exc:
            logger.info(f"exception occured while retrieving user portfolio {id = }")
            logger.exception(exc)
            raise exc


class UserPortfolioBySubscriptionId(GenericAPIView):
    """
    Update User Portfolio by Subscription Id
    """
    @swagger_auto_schema(request_body=user_portfolio_update_subscription_id_request_schema_dict,
                         manual_parameters=user_portfolio_update_subscription_id_path_request_schema_dict,
                         responses=user_portfolio_update_subscription_id_response_schema_dict)
    def put(self, request, subscription_id):
        try:
            logger.info(f"in user portfolio update by subscription_id api")
            request.data['subscription_id'] = subscription_id
            validator = UserPortfolioUpdateBySubscriptionIdValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            logger.info(f"User Portfolio update by subscription_id api {validated_data = }")
            updated_user_portfolio = update_user_portfolio_by_subscription_id(validated_data)
            read_ser = ReadUserPortfolioSerializer(updated_user_portfolio)
            return Response(read_ser.data)
        except Exception as exc:
            logger.info(f"exception occured while updating user portfolio {subscription_id = } in api")
            logger.exception(exc)
            raise exc


class ResetUserPortfolioOfUser(GenericAPIView):
    """
    Reset User Portfolio by Id
    """
    @swagger_auto_schema(operation_description='Reset User Portfolio of User',
                         request_body=user_portfolio_reset_request_schema_dict,
                         responses=reset_user_portfolio_response_schema_dict)
    def post(self, request):
        try:
            from apps.portfolio.models.user_portfolio import UserPortfolio
            logger.info(f"In reset user portfolio by id ")
            user_id = request.data['user_id']
            reset_user_portfolio_of_user(user_id)
            ret_dict = {
                "message": "User portfolio reset successful",
            }
            return Response(ret_dict)
        except Exception as exc:
            user_portfolio_id = request.data['user_portfolio_id']
            logger.info(f"Exception occurred while reseting user portfolio {user_portfolio_id = }")
            logger.exception(exc)
            raise exc


class UserPortfolioPositions(GenericAPIView):
    """
    Get User Portfolio Holdings for a user
    """

    @swagger_auto_schema(
        operation_description='Get User Portfolio Positions for a user',
        manual_parameters=user_portfolio_positions_schema_dict,
        responses=user_portfolio_positions_response_schema_dict
    )
    def get(self, request):
        try:
            logger.info(f"In User Portfolio Positions by user_id ")
            validator = UserPortfolioPositionParamsValidator(data=request.query_params)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            user_id = validated_data.get('user_id')
            basket_id = validated_data.get('basket_id')
            user_portfolio_positions = get_user_portfolio_positions_user(user_id, basket_id)
            read_ser = UserPortfolioPositionsSerializer(user_portfolio_positions, many=True)
            return Response(read_ser.data)
        except Exception as exc:
            logger.info(f"Error in getting user portfolio holdings in api")
            logger.exception(exc)
            raise exc


class UserPortfolioSummary(GenericAPIView):
    """
    API endpoint to fetch a summary of user portfolios including investment status.

    Query Parameters:
        - user_id (str): ID of the user
        - broker (str): Associated broker name
        - product_type (str): Product type (e.g., 'mtf')

    Returns:
        List[Dict]: Each dictionary contains user_portfolio_id, user_id, portfolio_id,
                    status, and is_invested flag.
    """

    @swagger_auto_schema(
        operation_description="Get User Portfolio Positions for a user",
        manual_parameters=user_portfolio_summary_params,
        responses=user_portfolio_summary_response_schema_dict
    )
    def get(self, request):
        """
        Handles GET request to fetch user portfolio summary.

        Validates query parameters and returns the portfolio summary for the given user.
        Logs detailed information for tracking and debugging.
        """
        try:
            logger.info("Received request to fetch user portfolio summary with params: %s", request.query_params)
            validator = UserPortfolioSummaryParamsValidator(data=request.query_params)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data

            logger.info("Validated parameters: %s", validated_data)
            user_portfolio_summary = fetch_user_portfolio_summary(**validated_data)
            return Response(user_portfolio_summary)
        except Exception as exc:
            logger.error("Error occurred while fetching user portfolio summary", exc_info=True)
            raise exc
