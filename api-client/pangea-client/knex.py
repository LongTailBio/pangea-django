
import requests

ENDPOINT = 'https://pangea.gimmebio.com/api'


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

    def __init__(self, endpoint_url=ENDPOINT):
        self.endpoint_url = endpoint_url
        self.auth = None
        self.headers = {'Accept': 'application/json'}

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
        self.auth = TokenAuth(response.json()['auth_token'])
        return self

    def get(self, url):
        response = requests.get(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
        )
        response.raise_for_status()
        return response.json()['results']

    def post(self, url, json={}):
        response = requests.post(
            f'{self.endpoint_url}/{url}',
            headers=self.headers,
            auth=self.auth,
            json=json
        )
        response.raise_for_status()
        return response.json()