"""
    API to retrieve User Rebalancing instruction
"""

import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.portfolio.apis.schemas.user_instruction import user_instruction_request_schema_dict, \
    user_instruction_response_schema_dict, update_trade_details_request_schema_dict
from apps.portfolio.apis.validators.user_instruction import UpdateTradeDetailsParamsValidator
from apps.portfolio.apis.validators.user_portfolio import UserPortfolioReqParamsValidator
from apps.portfolio.serializers.user_instruction import ReadUserInstructionSerializer
from apps.portfolio.services.user_instruction import get_user_rebalancing_instruction, update_trade_details

logger = logging.getLogger(__name__)


class UserInstruction(GenericAPIView):
    """
        Class for retrieving User Instruction
    """
    @swagger_auto_schema(operation_description='Retrieve User Instruction by ID', manual_parameters=user_instruction_request_schema_dict,responses=user_instruction_response_schema_dict)
    def get(self, request, id):
        try:
            logger.info(f"in get user rebalancing instruction api {id = }")
            validator = UserPortfolioReqParamsValidator(data={"id": id})
            validator.is_valid(raise_exception=True)
            user_rebalancing_instruction = get_user_rebalancing_instruction(id)
            logger.info(f"{user_rebalancing_instruction = }")
            read_ser = ReadUserInstructionSerializer(instance=user_rebalancing_instruction)
            return Response(read_ser.data)
        except Exception as exc:
            logger.info(f"exception occured while retrieving user rebalancing instruction {id = }")
            logger.exception(exc)
            raise exc


class TradeDetails(GenericAPIView):
    """
        Class for update trade details in user instruction
    """
    @swagger_auto_schema(request_body=update_trade_details_request_schema_dict)
    def put(self, request):
        """
            Updates the trade details received in the user instruction
            :return: Response object
        """
        logger.info("In TradeDetails API")
        validator = UpdateTradeDetailsParamsValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        validated_data = validator.validated_data
        logger.info(f"{validated_data = }")
        update_trade_details(validated_data)
        return Response({"data": "Details Updated"})
