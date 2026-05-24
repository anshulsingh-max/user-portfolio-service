# coding=utf-8
"""
Request Middleware
"""
import logging

logger = logging.getLogger(__name__)


class RequestMiddleWare:
    """
    Request Middleware Class
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # pylint: disable=W0703
        logger.debug("Request path = %s , request method = %s", request.path, request.method)
        if request.POST:
            logger.debug("POST=%s", request.POST)
        if request.GET:
            logger.debug("GET=%s", request.GET)

        return self.get_response(request)
