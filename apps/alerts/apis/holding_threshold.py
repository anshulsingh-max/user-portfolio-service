"""apps.alerts.apis.holding_threshold
-------------------------------
REST API view definitions for creating, retrieving and updating
`HoldingThreshold` objects. This module exposes a single
`HoldingThresholdView` class which inherits from DRF's
`GenericAPIView` and provides `POST`, `GET` and `PUT` handlers.

Endpoints
~~~~~~~~~
POST ``/alerts/holding-threshold``
    Create a new threshold. Expects a JSON body matching
    `HoldingThresholdParamsValidator`.

GET ``/alerts/holding-threshold``
    List thresholds filtered by query parameters handled by
    `HoldingThresholdQueryParamsValidator`.

PUT ``/alerts/holding-threshold``
    Update an existing threshold identified by the ``id`` field in
    the request body.

Each handler performs full validation, delegates the core business
logic to the dedicated *services* layer, serialises the resulting
model instances and returns a DRF `Response` object. Extensive
structured logging is performed for observability.
"""
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

import logging

from apps.alerts.apis.schemas.holding_threshold import (
    create_threshold_swagger_schema,
    create_threshold_swagger_response,
    get_holding_threshold_request_schema,
    get_holding_threshold_response_schema,
    update_threshold_request_body_schema,
    update_threshold_response_schema,
)
from apps.alerts.apis.validators.holding_threshold import (
    HoldingThresholdParamsValidator,
    HoldingThresholdQueryParamsValidator,
    UpdateHoldingThresholdSerializer,
)
from apps.alerts.serializers.holding_threshold import HoldingThresholdReadSerializer
from apps.alerts.services.holding_threshold import (
    create_holding_threshold,
    update_holding_threshold,
    fetch_holding_thresholds,
)

logger = logging.getLogger(__name__)


class HoldingThresholdView(GenericAPIView):
    """APIView responsible for **CRUD-style** interactions with
    `HoldingThreshold` resources.

    The class offers thin controller-style wrappers around the
    domain logic implemented in `apps.alerts.services.holding_threshold`.
    It ensures:

    * input validation via `rest_framework.serializers.Serializer`
    * delegation of business logic to the *services* module
    * output serialisation with `HoldingThresholdReadSerializer`
    * OpenAPI schema generation using ``drf-yasg`` helpers
    * structured logging for auditability
    """

    @swagger_auto_schema(
        request_body=create_threshold_swagger_schema,
        responses=create_threshold_swagger_response,
    )
    def post(self, request):
        """Create a `HoldingThreshold`.

        Parameters
        ----------
        request : rest_framework.request.Request
            Incoming HTTP request whose ``data`` attribute must contain the
            following JSON fields (see
            `HoldingThresholdParamsValidator` for the authoritative schema):

            * ``holding_type`` (str) – One of **ISIN**, **BASKET** …
            * ``holding_id`` (str) – Unique identifier of the holding item.
            * ``side`` (str) – Either ``BUY`` or ``SELL``.
            * ``source`` (str) – Upstream system origin.
            * ``threshold`` (Float) – Threshold percentage/absolute value.
            * ``effective_from`` (datetime) – When the threshold becomes active.

        Returns
        -------
        rest_framework.response.Response
            201-like response (DRF default) with the serialised
            `HoldingThreshold` in the body.

        Raises
        ------
        rest_framework.exceptions.ValidationError
            If the request body violates the validation rules.
        Exception
            Any unhandled exception will propagate after being logged; DRF will
            convert it to a 500 response.
        """
        try:
            logger.info("Received request to create HoldingThreshold", extra={"data": request.data})

            validator = HoldingThresholdParamsValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data

            threshold_obj = create_holding_threshold(validated_data)
            serializer = HoldingThresholdReadSerializer(instance=threshold_obj)

            logger.info(
                "Successfully created HoldingThreshold",
                extra={
                    "holding_type": threshold_obj.holding_type,
                    "holding_id": threshold_obj.holding_id,
                    "side": threshold_obj.side,
                    "source": threshold_obj.source,
                },
            )
            return Response(serializer.data)
        except Exception as exc:
            logger.info("Error while creating HoldingThreshold", exc_info=exc)
            logger.exception(exc)
            raise

    @swagger_auto_schema(
        manual_parameters=get_holding_threshold_request_schema,
        responses=get_holding_threshold_response_schema,
    )
    def get(self, request):
        """List `HoldingThreshold` objects.

        The query-string parameters are validated by
        `HoldingThresholdQueryParamsValidator` and translated into ORM filter
        keyword arguments.

        Parameters
        ----------
        request : rest_framework.request.Request
            The incoming HTTP request. Useful query parameters include but are
            not limited to ``holding_type``, ``holding_id``, ``side`` and
            ``source``.

        Returns
        -------
        rest_framework.response.Response
            A response containing **a list** of serialised thresholds ordered
            by ``-effective_from``.

        Raises
        ------
        rest_framework.exceptions.ValidationError
            For invalid query parameters.
        Exception
            Bubbled-up exceptions are logged and re-raised.
        """
        try:
            logger.info("Fetching HoldingThresholds with query params", extra={"params": request.GET.dict()})

            validator = HoldingThresholdQueryParamsValidator(data=request.GET)
            validator.is_valid(raise_exception=True)

            queryset = fetch_holding_thresholds(validator.filters)
            serializer = HoldingThresholdReadSerializer(queryset, many=True)
            logger.info("Successfully fetched HoldingThresholds")
            return Response(serializer.data)
        except Exception as exc:
            logger.info(f"Error while fetching HoldingThresholds: {exc}")
            logger.exception(exc)
            raise

    @swagger_auto_schema(
        request_body=update_threshold_request_body_schema,
        responses=update_threshold_response_schema,
    )
    def put(self, request):
        """Update an existing `HoldingThreshold`.

        The ID of the threshold to update must be supplied in the request
        payload under the ``id`` key. All other fields are optional; only the
        supplied ones will be updated.

        Parameters
        ----------
        request : rest_framework.request.Request
            HTTP request containing an ``id`` field and optionally any fields
            accepted by `UpdateHoldingThresholdSerializer`.

        Returns
        -------
        rest_framework.response.Response
            A response containing the updated serialised `HoldingThreshold`.

        Raises
        ------
        rest_framework.exceptions.ValidationError
            If validation fails (e.g., unknown ID or bad field values).
        apps.exceptions.NotFoundError
            If no `HoldingThreshold` with the provided ID exists.
        Exception
            Any other exception will be logged and re-raised.
        """
        threshold_id = request.data.get("id")
        logger.info("Updating HoldingThreshold", extra={"id": threshold_id})
        try:
            serializer = UpdateHoldingThresholdSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            threshold = update_holding_threshold(threshold_id, serializer.validated_data)
            resp_serializer = HoldingThresholdReadSerializer(instance=threshold)
            logger.info("Successfully updated HoldingThreshold", extra={"id": threshold_id})
            return Response(resp_serializer.data)
        except Exception as exc:
            logger.info(f"Error while updating HoldingThreshold: {exc}")
            logger.exception(exc)
            raise
