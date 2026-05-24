"""
API module for handling order-related actions.

This module contains API views for performing operations on orders, such as
retrieving canceled order instructions and creating retry instructions.
"""

import logging
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.portfolio.constants import OrderCurrentStatus
from apps.portfolio.services.order_instructions import get_cancelled_instructions, create_retry_instructions
from apps.portfolio.services.orders import skip_orders

logger = logging.getLogger(__name__)


class RetryOrder(GenericAPIView):
    """
    API view to handle retrying canceled orders.

    The `RetryOrder` view allows users to create new retry instructions for
    orders that were previously canceled within a specific basket. It retrieves
    the latest canceled instructions for the given basket and attempts to
    recreate them.

    Methods:
        post(request, basket_id): Handles the POST request to retry canceled orders.

    Args:
        request (Request): The request object containing data and metadata.
        basket_id (int): The ID of the basket for which the retry operation is requested.

    Returns:
        Response: A JSON response with the newly created retry instructions.
    """

    def post(self, request, basket_id):
        """
        Handle POST requests to retry canceled orders for a basket.

        This method retrieves the latest canceled instructions for the specified
        `basket_id`, recreates those instructions, and returns the newly created
        retry instructions as a response.

        Args:
            request (Request): The request object containing the request data.
            basket_id (int): The ID of the basket for which retry instructions are to be created.

        Returns:
            Response: A response containing a list of newly created retry instructions.

        Raises:
            Exception: If an error occurs during the retry process, it logs the exception and re-raises it.
        """
        try:
            logger.info(f"In RetryOrder for {basket_id =}")
            cancelled_instructions = get_cancelled_instructions(basket_id)
            instructions = create_retry_instructions(cancelled_instructions)
            return Response(instructions)
        except Exception as exc:
            logger.info(f"Error while retrying orders: {exc}")
            logger.exception(exc)
            raise exc


class SkipOrder(GenericAPIView):
    """
    API view to skip all orders associated with a specific basket by updating their
    statuses to 'SKIP'.

    This view handles a POST request that takes in a `basket_id`, and for all orders
    within the basket, it updates the status to 'SKIP' using the `skip_orders` function.

    Args:
        basket_id (int): The ID of the basket for which the orders need to be skipped.

    Returns:
        Response: A success message indicating that the details were updated if the
        operation was successful. In case of an exception, the exception is logged,
        and a raised error will trigger the default DRF error handling.

    Example:
        POST /api/skip-order/{basket_id}/
    """

    def post(self, request, basket_id):
        try:
            logger.info(f"In SkipOrder for {basket_id =}")
            skip_orders(basket_id=basket_id, new_status=OrderCurrentStatus.SKIP.value)
            return Response({"data": "Details Updated"})
        except Exception as exc:
            logger.error(f"Error while skipping orders for basket {basket_id}: {exc}")
            logger.exception(exc)
            raise exc
