import logging
import time

import requests
import os

from multitenant.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class APIClient:

    def __init__(self, name):
        self.name = name
        self.tenant_id = get_current_tenant() or "default"

    def _update_headers(self, headers: dict|None = None) -> dict:
        headers = headers or {}
        if self.tenant_id:
            headers['X-Tenant-ID'] = self.tenant_id
        return headers

    def _get(self, url, headers=None, params={}):
        try:
            headers=self._update_headers(headers)
            start = time.time()
            logger.info(f"{url=} {params=}")
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                end = time.time()
                time_taken = end - start
                logger.info(f"{time_taken =}s")
                # logger.info(f"{time_taken =}s {response.json()=}")
                return response.json()
            else:
                logger.info(f"{response.status_code=} {response.json()}")
        except Exception as exc:
            logger.exception(exc)
            raise exc

    def _put(self, url, headers=None, data=None, params=None):
        try:
            start = time.time()
            headers = self._update_headers(headers)
            logger.info(f"{url=} {data=}")
            response = requests.put(url, headers=headers, json=data, params=params)
            if response.status_code == 200:
                end = time.time()
                time_taken = end - start
                logger.info(f"{time_taken =}s")
                # logger.info(f"{time_taken =}s {response.json()=}")
                return response.json()
            else:
                logger.info(f"{response.status_code=} {response.json()}")
                raise Exception(response.json()["details"])
        except Exception as exc:
            logger.exception(exc)
            raise exc

    def _post(self, url, headers=None, data=None, params=None):
        try:
            start = time.time()
            headers = self._update_headers(headers)
            logger.info(f"{url=} {data=}, {params =}")
            response = requests.post(url, headers=headers, json=data, params=params)
            if response.status_code == 200:
                end = time.time()
                time_taken = end - start
                logger.info(f"{time_taken =}s")
                # logger.info(f"{time_taken =}s {response.json()=}")
                return response.json()
            else:
                logger.info(f"{response.status_code=} {response.json()}")
                raise Exception(response.json()["details"])
        except Exception as exc:
            logger.exception(exc)
            raise exc