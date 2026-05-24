"""
basket.py

This module defines the Basket API endpoint for creating user baskets.
It utilizes Django REST Framework's GenericAPIView to handle POST requests
for basket creation. The API validates input data, creates a basket, and
returns the created basket's details along with appropriate HTTP responses.
"""

import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from apps.portfolio.apis.schemas.basket import create_basket_swagger_schema, create_basket_swagger_response, \
    get_basket_request_schema, get_basket_response_schema, update_basket_request_schema, update_basket_response_schema, \
    get_basket_details_schema
from apps.portfolio.apis.validators.basket import CreateBasketParamsValidator, BasketQueryParamsValidator, \
    UpdateBasketFieldsValidator, BasketDetailsRequestValidator
from apps.portfolio.serializers.basket import BasketSerializer, BasketReadSerializer
from apps.portfolio.services.basket import create_basket, get_basket_details, update_basket
from apps.portfolio.models.basket import Basket as BasketModel

logger = logging.getLogger(__name__)


class Basket(GenericAPIView):
    """

    This endpoint allows users to create a new basket by providing the necessary
    parameters. It validates the input data, creates the basket, and returns the
    created basket details in the response.

    Methods:
        post(request): Handles POST requests to create a new basket.
        get(rquest): Handles GET request to get basket details for given user and state.
    """

    @swagger_auto_schema(
        request_body=create_basket_swagger_schema,
        responses=create_basket_swagger_response
    )
    def post(self, request):
        """
        Handle POST requests to create a new basket.

        Args:
            request (Request): The request object containing input data.

        Returns:
            Response: A response object containing the created basket details
            and HTTP status code.

        Raises:
            Exception: Raises any exceptions encountered during the basket
            creation process, which are logged for debugging purposes.
        """
        try:
            logger.info(f"Creating basket with {request.data =}")
            validator = CreateBasketParamsValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            basket_obj = create_basket(validated_data)
            ser = BasketReadSerializer(instance=basket_obj)
            return Response(ser.data, status=201)
        except Exception as exc:
            logger.info(f"Error while creating basket: {exc =}")
            logger.exception(exc)
            raise exc

    @swagger_auto_schema(
        manual_parameters=get_basket_request_schema,
        responses=get_basket_response_schema
    )
    def get(self, request):
        """
        This method processes incoming requests to fetch details of baskets based on
        specified query parameters. It validates the parameters, retrieves the relevant
        basket details, and returns the data in the response.

        Args:
            request (Request): The HTTP request object containing query parameters.

        Returns:
            Response: A response object containing the serialized basket details
            and HTTP status code.

        Raises:
            ValidationError: If the provided query parameters are invalid.
            Exception: Any other exceptions encountered during the basket retrieval
            process, which are logged for debugging purposes.
        """
        try:
            logger.info("Getting basket details")
            validator = BasketQueryParamsValidator(data=request.GET)
            validator.is_valid(raise_exception=True)
            validated_params = validator.validated_data
            basket_query_set = get_basket_details(
                user_id=validated_params.get('user_id'),
                current_state=validated_params.get('current_state')
            )
            ser = BasketReadSerializer(instance=basket_query_set, many=True)
            return Response(ser.data)
        except Exception as exc:
            logger.info(f"Error while getting basket details: {exc}")
            logger.exception(exc)
            raise exc

    @swagger_auto_schema(
        request_body=update_basket_request_schema,
        responses=update_basket_response_schema
    )
    def put(self, request):
        """
        Handles the HTTP PUT request to update a Basket instance with the provided data.
        The method validates the input data using the UpdateBasketFieldsValidator and
        updates the corresponding Basket instance with non-null fields.

        Args:
            request (Request): The HTTP request object containing the data to update the basket.

        Returns:
            Response: A serialized representation of the updated Basket instance.

        Raises:
            Exception: If any error occurs during the update process.
        """
        basket_id = request.data.get('id')
        try:
            logger.info(f"Updating basket details for {basket_id =}")

            validator = UpdateBasketFieldsValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            basket_instance = update_basket(basket_id, validated_data)
            ser = BasketReadSerializer(instance=basket_instance)
            return Response(ser.data)
        except Exception as exc:
            logger.info(f"Error while updating basket data: {exc}")
            logger.exception(exc)
            raise exc


class BasketDetails(GenericAPIView):
    """
    API view to fetch details of a basket based on the provided basket ID and recommendation ID.

    - Uses the BasketDetailsRequestValidator to validate incoming request data.
    - Retrieves the BasketModel instance based on the provided basket ID and recommendation ID.
    - Serializes the basket instance using BasketReadSerializer and returns the serialized data.

    Exceptions:
        - If validation fails, a 400 response is returned with the appropriate validation error messages.
        - If the basket is not found or any other exception occurs, an error is logged, and the exception is raised.

    Request body schema:
        - Defined by `get_basket_details_schema` using Swagger documentation for better API visibility.

    Logging:
        - Logs incoming request data and exceptions for better traceability.

    HTTP Method: POST
    """

    @swagger_auto_schema(
        request_body=get_basket_details_schema
    )
    def post(self, request):
        try:
            logger.info(f"In BasketDetails {request.data =}")
            validator = BasketDetailsRequestValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data
            basket_instance = BasketModel.objects.get(id=validated_data.get("basket_id"),
                                                      recommendation_id=validated_data.get("recommendation_id")
                                                      )
            ser = BasketReadSerializer(instance=basket_instance)
            return Response(ser.data)
        except Exception as exc:
            logger.info(f"Error while fetching basket details: {exc}")
            logger.exception(exc)
            raise exc


class BasketById(GenericAPIView):
    """
    API View to retrieve details of a specific basket by its ID.

    This endpoint fetches a basket's details from the database using its unique ID
    and serializes the data for the response.

    Methods:
    --------
    get(request, basket_id):
        Handles GET requests to fetch the basket details.

    Parameters:
    -----------
    request: HttpRequest
        The HTTP request object.
    basket_id: int
        The unique identifier of the basket.

    Returns:
    --------
    Response
        Serialized basket data if the operation is successful.

    Raises:
    -------
    Exception
        If there is any issue during the data retrieval or serialization process.
    """

    def get(self, request, basket_id):
        try:
            logger.info(f"Fetching details for basket with ID: {basket_id}")
            basket_instance = BasketModel.objects.get(id=basket_id)
            logger.info(f"Basket with ID {basket_id} successfully retrieved")
            ser = BasketReadSerializer(instance=basket_instance)
            logger.info(f"Serialized data for basket with ID {basket_id} successfully generated")
            return Response(ser.data)
        except Exception as exc:
            logger.error(f"An error occurred while fetching basket details for ID {basket_id}: {exc}")
            logger.exception(exc)
            raise exc
