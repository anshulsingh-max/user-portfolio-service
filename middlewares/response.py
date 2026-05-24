# coding=utf-8
"""
Response Middleware
"""
import json
import logging

from middlewares.constants import UI_PATHS

logger = logging.getLogger(__name__)


class ResponseMiddleWare:
    """
    Response Middleware Class
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        # pylint: disable=protected-access
        """
             Function to update response
         """
        if 'content-type' in response.headers:
            logger.debug("response content type = %s ", response.headers["content-type"])
        if response.status_code in [400, 401, 422]:
            response.data['error'] = True
            response._is_rendered = False
            response.render()

        intersecting_path = set(request.path.split('/')).intersection(UI_PATHS)
        if not intersecting_path and response.status_code in [200, 201] and hasattr(response, 'data'):
            if request.method in ["POST", "PUT", "PATCH"] and request.body:
                try:
                    pay_load = json.loads(request.body)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON payload in request body.")
                    pay_load = {}
            else:
                pay_load = request.GET

            response.data = {
                'data': response.data,
                'error': False,
                'payload': pay_load
            }
            response._is_rendered = False
            response.render()

        if 'content-type' in response.headers and "json" in response.headers["content-type"]:
            logger.debug("response = %s", response.content[:200])
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        logger.debug("API complete")
        return response
