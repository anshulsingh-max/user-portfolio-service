# coding=utf-8
"""
Middleware for handling exceptions
"""

import logging
import traceback

from django.conf import settings
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from rest_framework.views import exception_handler

from apps.exceptions.user_portfolio import UserPortfolioNotFound, UserInstructionNotFound
from apps.utils.notifications import Notifications
from middlewares.constants import SERVICE

logger = logging.getLogger(__name__)

notification = Notifications(title=SERVICE)

class ExceptionMiddleWare:
    """
    Exception middleware
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """
        Process Exception
        :param request:
        :param exception:
        :return:
        """
        logger.info("request.path %s", request.path)
        logger.error("error: %s", traceback.format_exc())
        return self.handle_exception(request, exception)

    def handle_exception(self, request, exception):
        """
        Handle Exception
        :param request:
        :param exception:
        :return:
        """
        logger.info(f"{request = }")
        logger.exception(exception)
        message = exception.message if hasattr(exception, 'message') else str(exception)
        code = f'{settings.APP_NAME}_{(exception.code if hasattr(exception, "code") else 101)}'
        if isinstance(exception, (UserInstructionNotFound, UserPortfolioNotFound)):
            logger.info("In UserInstructionNotFound/UserPortfolioNotFound")
            generic_message = "Not Found"
            response = {'error': True, 'message': generic_message, 'details': message,
                        'code': code}
            status = HTTP_404_NOT_FOUND
        elif isinstance(exception, ValidationError):
            logger.info("In ValidationError")
            generic_message = "Some error occurred"
            response = {'error': True, 'message': generic_message, "details": message,
                        'code': code}

            status = HTTP_400_BAD_REQUEST

        else:
            logger.info("In general Exception")
            generic_message = "Something went wrong while processing the request, our team is looking into it."
            response = {'error': True, 'message': generic_message, "details": message,
                        'code': code}
            status = HTTP_422_UNPROCESSABLE_ENTITY
        notification.notify_error(message=request.path,
                                  summary=str(response),
                                  request_id=request.id)
        return JsonResponse(response, status=status)


def get_request_url(request):
    """Utility function to get the URL from the request."""
    try:
        scheme = request.scheme
        domain = request.get_host()
        path = request.get_full_path()
        full_url = f"{scheme}://{domain}{path}"
        return full_url
    except Exception as exc:
        logger.exception(exc)
        return None


def rest_exception_handler(exc, context):
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    """
    response = exception_handler(exc, context)
    logger.exception(exc)
    if response is not None:
        request = context.get('request')
        request_url = get_request_url(request) if request else None
        for key, errors in response.data.items():
            error_message = f"{key}-"
            for error in errors:
                error_message += error
            break

        generic_message = "Some error occurred"
        code = f'{settings.APP_NAME}_{(exc.code if hasattr(exc, "code") else 101)}'
        response = {'error': True, 'message': generic_message, "details": error_message,
                    'code': code}
        status = 400
        notification.notify_error(message=f"API Endpoint: {request_url}",
                                  summary=str(response),
                                  request_id=context['request'].id)
        return JsonResponse(response, status=status)
    return response
