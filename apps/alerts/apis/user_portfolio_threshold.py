from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

import logging

from apps.alerts.apis.schemas.user_portfolio_threshold import create_threshold_swagger_schema, \
    create_threshold_swagger_response, get_user_portfolio_threshold_request_schema, \
    get_user_portfolio_threshold_response_schema, update_threshold_request_body_schema, update_threshold_response_schema
from apps.alerts.apis.validators.user_portfolio_threshold import UserPortfolioThresholdParamsValidator, \
    UserPortfolioThresholdQueryParamsValidator, UpdateUserPortfolioThresholdSerializer
from apps.alerts.models import UserPortfolioThreshold
from apps.alerts.serializers.user_portfolio_threshold import (
    UserPortfolioThresholdReadSerializer,
    UserPortfolioThresholdWithHoldingsSerializer,
)
from apps.alerts.services.user_portfolio_threshold import create_user_portfolio_threshold, \
    update_user_portfolio_threshold

logger = logging.getLogger(__name__)


class UserPortfolioThresholdView(GenericAPIView):
    """
    API endpoint to manage User Portfolio Thresholds.

    This endpoint allows users (or admins in rare cases) to set and manage
    portfolio thresholds. A threshold represents certain risk/limit parameters
    (e.g., stop-loss, investment cap) tied to a user's portfolio. At any
    given time, only one threshold is active per portfolio.

    Methods:
        post(request): Create a new threshold for a user's portfolio.
    """

    @swagger_auto_schema(
        request_body=create_threshold_swagger_schema,
        responses=create_threshold_swagger_response
    )
    def post(self, request):
        """
        Create a new User Portfolio Threshold.

        This endpoint accepts user or admin-defined threshold parameters
        for a given portfolio. The request data is validated before creating
        the threshold. At any point, only one threshold is active for a
        portfolio.

        Example use cases:
        - First-time user sets portfolio thresholds.
        - User updates thresholds later.
        - Admin overrides thresholds in rare scenarios.

        Args:
            request (Request): Incoming HTTP request with threshold parameters.

        Returns:
            Response: JSON response containing created threshold details
            and HTTP 201 status code on success.

        Raises:
            ValidationError: If request payload is invalid.
            Exception: Any unexpected error during threshold creation is logged
            and re-raised for visibility.
        """
        try:
            logger.info(f"Received request to create UserPortfolioThreshold with data={request.data}")

            validator = UserPortfolioThresholdParamsValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data

            threshold_obj = create_user_portfolio_threshold(validated_data)
            serializer = UserPortfolioThresholdReadSerializer(instance=threshold_obj)
            logger.info("Successfully created UserPortfolioThreshold")
            return Response(serializer.data)

        except Exception as exc:
            logger.info(f"Error while creating UserPortfolioThreshold: {exc}")
            logger.exception(exc)
            raise exc

    @swagger_auto_schema(
        manual_parameters=get_user_portfolio_threshold_request_schema,
        responses=get_user_portfolio_threshold_response_schema
    )
    def get(self, request):
        """
        Retrieve thresholds for a user's portfolio.

        Query params are validated via `UserPortfolioThresholdQueryParamsValidator`.
        Only filters with provided values are applied.

        Args:
            request (Request): Incoming HTTP request with query parameters.

        Returns:
            Response: JSON response containing filtered threshold details.
        """
        try:
            logger.info("Fetching UserPortfolioThresholds")

            validator = UserPortfolioThresholdQueryParamsValidator(data=request.GET)
            validator.is_valid(raise_exception=True)

            instance = UserPortfolioThreshold.objects.get(**validator.filters)
            serializer = UserPortfolioThresholdWithHoldingsSerializer(
                instance,
                context={"filters": validator.filters}
            )
            logger.info("Successfully fetched UserPortfolioThresholds")
            return Response(serializer.data)
        except UserPortfolioThreshold.DoesNotExist:
            logger.info("UserPortfolioThreshold not found. Returning empty dict")
            return Response({})
        except Exception as exc:
            logger.info(f"Error while fetching UserPortfolioThresholds: {exc}")
            logger.exception(exc)
            raise exc

    @swagger_auto_schema(
        request_body=update_threshold_request_body_schema,
        responses=update_threshold_response_schema
    )
    def put(self, request):
        """
        Update an existing UserPortfolioThreshold instance.

        This endpoint allows updating selective fields of a UserPortfolioThreshold.
        Only the fields provided in the request body are updated. The allowed fields are:
            - `target_pct` (Float): Percentage-based threshold.
            - `status` (str): Threshold status, either 'active' or 'inactive'.
            - `source` (str): Origin of the update, one of 'user', 'admin', or 'dealer'.

        The update is performed within a database transaction to ensure atomicity.
        Existing thresholds can be deactivated by setting `status` to 'inactive'.

        Example request payload:
        {
            "id": 123,
            "target_pct": 0.05,
            "status": "inactive",
            "source": "admin"
        }

        Args:
            request (Request): DRF request object containing JSON body with the
                fields to update. Must include 'id' to identify the threshold.

        Returns:
            Response: JSON response containing the updated UserPortfolioThreshold
                data serialized via `UserPortfolioThresholdReadSerializer`.

        Raises:
            ValidationError: If request payload fails serializer validation.
            UserPortfolioThreshold.DoesNotExist: If no threshold exists for the given ID.
            Exception: Any unexpected error during update, which is logged for debugging.
        """
        threshold_id = request.data.get('id')
        logger.info(f"Updating UserPortfolioThreshold {threshold_id =}")
        try:
            serializer = UpdateUserPortfolioThresholdSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            threshold = update_user_portfolio_threshold(threshold_id, serializer.validated_data)
            resp_serializer = UserPortfolioThresholdReadSerializer(instance=threshold)
            logger.info(f"Successfully updated UserPortfolioThreshold {threshold_id =}")
            return Response(resp_serializer.data)
        except Exception as exc:
            logger.info(f"Error while updating UserPortfolioThreshold: {exc}")
            logger.exception(exc)
            raise exc
