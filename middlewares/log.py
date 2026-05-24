
"""
Middleware to log APIs requests and responses.
"""
import socket
import time
import json
import logging

from middlewares.constants import UI_PATHS, EXCLUDED_PATHS

request_logger = logging.getLogger(__name__)


class RequestResponseLogMiddleware:
    """Request Logging Middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        intersecting_path = set(request.path.split('/')).intersection(UI_PATHS)
        if intersecting_path:
            return self.get_response(request)

        start_time = time.time()
        log_data = {
            "remote_address": request.META["REMOTE_ADDR"],
            "server_hostname": socket.gethostname(),
            "request_method": request.method,
            "request_path": request.get_full_path(),
        }
        if request.method in ['POST', 'PUT', 'PATCH'] and request.META['PATH_INFO'] not in EXCLUDED_PATHS:
            req_body = json.loads(request.body.decode("utf-8")) if request.body else {}
            log_data["request_body"] = req_body

        # request passes on to controller
        response = self.get_response(request)

        log_data['response_status'] = response.status_code

        # add response body to log_data
        if response:
            try:
                response_body = json.loads(response.content.decode("utf-8"))
                log_data["response_body"] = response_body
            except ValueError:
                log_data["response_body"] = response.content

        log_data["run_time"] = time.time() - start_time
        request_logger.info(msg=log_data)

        return response
