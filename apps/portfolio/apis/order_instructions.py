"""
API for handling order instructions within the basket.

This module defines a view to create new order instructions based on incoming requests.
It validates the request data, creates the order instructions using the service layer, and
returns a serialized response with the created instructions.

Attributes:
    logger (Logger): A logger for capturing events within the API.
"""

import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.portfolio.apis.schemas.order_instructions import create_order_instructions_schema
from apps.portfolio.apis.schemas.user_instruction import update_trade_details_request_schema_dict
from apps.portfolio.apis.validators.order_instructions import CreateOrderInstructionsValidator, \
    UpdateOrderInstructionsValidator
from apps.portfolio.serializers.order_instructions import OrderInstructionSerializer
from apps.portfolio.services.order_instructions import create_order_instructions
from apps.portfolio.services.user_instruction import update_order_instructions

logger = logging.getLogger(__name__)


class OrderInstructions(GenericAPIView):
    """
    API View for creating order instructions.

    This view handles POST requests for creating order instructions.
    It validates the incoming data, calls the service layer to process the order instructions,
    and returns the serialized response.

    Methods:
        post(request): Handles the creation of new order instructions.
    """
    @swagger_auto_schema(
        request_body=create_order_instructions_schema,
        responses={}
    )
    def post(self, request):
        """
        Handles POST requests for creating order instructions.

        This method:
            - Validates the incoming request data using the `CreateOrderInstructionsValidator`.
            - Calls the `create_order_instructions` service to create the order instructions.
            - Serializes the created order instruction object using `OrderInstructionSerializer`.
            - Returns a JSON response containing the serialized order instructions with a 201 status code.

        In case of any exceptions, it logs the error and raises the exception.

        Args:
            request (Request): The incoming request object containing the order instructions data.

        Returns:
            Response: A response object with the serialized data of the created order instructions.
        """
        try:
            logger.info(f"In create order instructions")
            validator = CreateOrderInstructionsValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_order_instructions = validator.validated_data
            order_instruction_obj = create_order_instructions(validated_order_instructions.get('instructions'))
            ser = OrderInstructionSerializer(instance=order_instruction_obj, many=True)
            return Response(ser.data, status=201)
        except Exception as exc:
            logger.info(f"Error while creating order instructions {exc =}")
            logger.exception(exc)
            raise exc


class UpdateOrderInstructions(GenericAPIView):
    """
    API endpoint to update order instructions for a specific trade placement.

    This endpoint processes a PUT request with trade order update details,
    validates the input using `UpdateOrderInstructionsValidator`, and updates
    the order instructions accordingly.

    HTTP Method:
        - PUT

    Request Body:
        - Expects a JSON payload with the following fields:
            - trade_placement_id (int, optional): The unique ID of the trade placement.
            - order_tag (str, required): A tag or identifier for the order.
            - symbol (str, required): The trading symbol for the order.
            - quantity (float, required): The total quantity of the order.
            - filled_quantity (float, required): The quantity of the order already filled.
            - side (str, required): The side of the order ("buy" or "sell").
            - value (float, optional): The value of the order.
            - status (str, required): The current status of the order.
            - reason (str, optional): The reason for the order status.

    Returns:
        - HTTP 200: Successful update with a JSON response:
            {
                "data": "Details Updated"
            }
        - HTTP 400: Validation error with details of the failed fields.

    Example Request:
        PUT /api/orders/instructions/update
        {
            "trade_placement_id": 123,
            "order_tag": "ORDER_001",
            "symbol": "AAPL",
            "quantity": 100.0,
            "filled_quantity": 50.0,
            "side": "buy",
            "value": 15000.0,
            "status": "completed",
            "reason": "Order partially filled"
        }

    Example Response:
        {
            "data": "Details Updated"
        }

    Swagger Schema:
        - Uses `update_trade_details_request_schema_dict` for Swagger documentation.

    Raises:
        - ValidationError: If the input data does not pass validation.
        - Exception: Any other exceptions are logged.

    """
    @swagger_auto_schema(request_body=update_trade_details_request_schema_dict)
    def put(self, request):
        logger.info("In TradeDetails API")

        validator = UpdateOrderInstructionsValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        validated_data = validator.validated_data
        logger.info(f"Validated data: {validated_data}")
        update_order_instructions(validated_data)
        return Response({"data": "Details Updated"})
