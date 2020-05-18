from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions


class TokenParamAuthentication(authentication.TokenAuthentication):

    def authenticate(self, request):
        try:
            params = request.query_params.copy()
            token = params.pop('token')[0]
            request.META['HTTP_AUTHORIZATION'] = f'Token {token}'
        except KeyError:
            pass

        return super(TokenParamAuthentication, self).authenticate(request)
