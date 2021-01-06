import os
import requests
import logging
import json
from time import time
from glob import glob

from .file_system_cache import FileSystemCache

DEFAULT_ENDPOINT = 'https://pangea.gimmebio.com'


logger = logging.getLogger(__name__)  # Same name as calling module
logger.addHandler(logging.NullHandler())  # No output unless configured by calling program


def clean_url(url):
    if url[-1] == '/':
        url = url[:-1]
    return url


class TokenAuth(requests.auth.AuthBase):
    """Attaches MetaGenScope Token Authentication to the given Request object."""

    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        """Add authentication header to request."""
        request.headers['Authorization'] = f'Token {self.token}'
        return request

    def __str__(self):
        """Return string representation of TokenAuth."""
        return self.token


class Knex:

    def __init__(self, endpoint_url=DEFAULT_ENDPOINT):
        self.endpoint_url = endpoint_url
        self.endpoint_url += '/api'
        self.auth = None
        self.headers = {'Accept': 'application/json'}
        self.cache = FileSystemCache()

    def _logging_info(self, **kwargs):
        base = {'endpoint_url': self.endpoint_url, 'headers': self.headers}
        base.update(kwargs)
        return base

    def _clean_url(self, url):
        url = clean_url(url)
        url = url.replace(self.endpoint_url, '')
        if url[0] == '/':
            url = url[1:]
        return url

    def add_auth_token(self, token):
        self.auth = TokenAuth(token)

    def login(self, username, password):
        d = self._logging_info(email=username, password='*' * len(password))
        logger.debug(f'Sending log in request. {d}')
        blob = self.cache.get_cached_blob(username)
        if not blob:
            response = requests.post(
                f'{self.endpoint_url}/auth/token/login',
                headers=self.headers,
                json={
                    'email': username,
                    'password': password,
                }
            )
            response.raise_for_status()
            logger.debug(f'Received log in response. {response.json()}')
            blob = response.json()
            self.cache.cache_blob(username, blob)
        self.add_auth_token(blob['auth_token'])
        return self

    def _handle_response(self, response, json_response=True):
        try:
            response.raise_for_status()
        except:
            logger.debug(f'Request failed. {response}\n{response.content}')
            raise
        if json_response:
            return response.json()
        return response

    def get(self, url, **kwargs):
        url = self._clean_url(url)
        d = self._logging_info(url=url, auth_token=self.auth)
        logger.debug(f'Sending GET request. {d}')
        response = requests.get(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
        )
        return self._handle_response(response, **kwargs)

    def post(self, url, json={}, **kwargs):
        url = self._clean_url(url)
        d = self._logging_info(url=url, auth_token=self.auth, json=json)
        logger.debug(f'Sending POST request. {d}')
        response = requests.post(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
            json=json
        )
        return self._handle_response(response, **kwargs)

    def put(self, url, json={}, **kwargs):
        url = self._clean_url(url)
        d = self._logging_info(url=url, auth_token=self.auth, json=json)
        logger.debug(f'Sending PUT request. {d}')
        response = requests.put(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
            json=json
        )
        return self._handle_response(response, **kwargs)

    def patch(self, url, json={}, **kwargs):
        url = self._clean_url(url)
        d = self._logging_info(url=url, auth_token=self.auth, json=json)
        logger.debug(f'Sending PATCH request. {d}')
        response = requests.patch(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
            json=json
        )
        return self._handle_response(response, **kwargs)

    def delete(self, url, **kwargs):
        url = self._clean_url(url)
        d = self._logging_info(url=url, auth_token=self.auth)
        logger.debug(f'Sending DELETE request. {d}')
        response = requests.delete(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
        )
        return self._handle_response(response, **kwargs)
