
import requests

DEFAULT_ENDPOINT = 'https://pangea.gimmebio.com'


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

    def add_auth_token(self, token):
        self.auth = TokenAuth(token)

    def login(self, username, password):
        response = requests.post(
            f'{self.endpoint_url}/auth/token/login',
            headers=self.headers,
            json={
                'email': username,
                'password': password,
            }
        )
        response.raise_for_status()
        self.add_auth_token(response.json()['auth_token'])
        return self

    def get(self, url):
        response = requests.get(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
        )
        response.raise_for_status()
        return response.json()

    def post(self, url, json={}):
        response = requests.post(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
            json=json
        )
        response.raise_for_status()
        return response.json()

    def put(self, url, json={}):
        response = requests.put(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
            json=json
        )
        response.raise_for_status()
        return response.json()

    def delete(self, url):
        response = requests.delete(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
        )
        response.raise_for_status()
        return response.json()
