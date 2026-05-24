import logging

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.alerts.apis.validators.stop_loss_alert import StopLossAlertQueryParamsValidator
from apps.alerts.apis.validators.loss_limit_update import LossLimitUpdateValidator
from apps.alerts.services.stop_loss_alert import get_stop_loss_alerts
from apps.alerts.tasks.loss_limit_updated_notification import send_loss_limit_updated_notification
from apps.alerts.apis.schemas.losslimitupdate import loss_limit_updated_notification_request_body, \
    loss_limit_updated_notification_response_body, stop_loss_constituents_request_body, \
    stop_loss_constituents_response_body

from multitenant.tenant_context import get_current_tenant
logger = logging.getLogger(__name__)


class StopLossConstituents(GenericAPIView):
    """
    API view to retrieve holdings that have hit their stop loss thresholds.

    GET Parameters:
        user_portfolio_id (int): The user portfolio ID to check for stop loss alerts

    Returns:
        List of holdings with stop loss hit, including:
        - symbol: Stock symbol
        - target_pct: Stop loss percentage threshold
        - avg_buy_price: Average purchase price
        - stop_loss_price: Calculated stop loss price
        - live_price: Current live price
    """

    @swagger_auto_schema(
        operation_description='GET Stop Loss Alerts for User Portfolio',
        manual_parameters=stop_loss_constituents_request_body,
        responses=stop_loss_constituents_response_body
    )
    def get(self, request):
        """
        Retrieve stop loss alerts for a user portfolio.

        Returns a list of holdings that have hit their stop loss thresholds.
        """
        try:
            logger.info("In stop loss alerts GET API")

            # Validate input parameters
            validator = StopLossAlertQueryParamsValidator(data=request.GET)
            validator.is_valid(raise_exception=True)
            validated_data = validator.validated_data

            # Get stop loss alerts from service
            user_portfolio_id = validated_data.get('user_portfolio_id')
            alerts = get_stop_loss_alerts(user_portfolio_id)

            logger.info("Successfully retrieved stop loss alerts for user_portfolio_id=%s, count=%s",
                       user_portfolio_id, len(alerts))
            return Response(alerts)

        except Exception as exc:
            logger.exception("Error while retrieving stop loss alerts")
            raise exc


class LossLimitUpdatedNotification(GenericAPIView):
    """
    API view to trigger a loss limit updated notification for a user portfolio.
    """

    @swagger_auto_schema(
        operation_description="Trigger loss limit updated notification",
        request_body=loss_limit_updated_notification_request_body,
        responses=loss_limit_updated_notification_response_body
    )
    def post(self, request):
        """
        Trigger a celery task to publish the loss limit updated event.
        """
        # Validate input parameters
        validator = LossLimitUpdateValidator(data=request.data)
        validator.is_valid(raise_exception=True)
        validated_data = validator.validated_data

        user_portfolio_id = validated_data.get("user_portfolio_id")
        loss_limit = validated_data.get("loss_limit")

        logger.info(
            "Received loss limit updated notification trigger for user_portfolio_id=%s",
            user_portfolio_id,
        )
        tenant_id=get_current_tenant()
        send_loss_limit_updated_notification.delay(user_portfolio_id, loss_limit=loss_limit,tenant_id=tenant_id)
        return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)
