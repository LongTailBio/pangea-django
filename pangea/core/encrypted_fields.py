"""Encrypted Model Fields.

From https://github.com/defrex/django-encrypted-fields with modifications.
"""

import types

from django.db import models
from django.conf import settings

from itertools import cycle
import base64


class EncryptedFieldException(Exception):
    pass


class XOR:
    """Does this count as rolling my own crypto?
    I can't find any good python libraries and XOR is dummy simple.
    """

    @staticmethod
    def key():
        mykey = settings.SECRET_KEY
        assert mykey
        return mykey

    @staticmethod
    def encrypt(data):
        key = XOR.key()
        xored = [chr(ord(x) ^ ord(y)) for (x, y) in zip(data, cycle(key))]
        xored = ''.join(xored)
        xored = xored.encode('utf-8')
        xored = base64.standard_b64encode(xored)
        return xored.decode('utf-8')

    @staticmethod
    def decrypt(data):
        key = XOR.key()
        data = data.encode('utf-8')
        data = base64.standard_b64decode(data)
        xored = [chr(x ^ ord(y)) for (x, y) in zip(data, cycle(key))]
        xored = ''.join(xored)
        return xored


class EncryptedString:
    """Ensures that we will need to manually call `decrypt` to access the plain text."""

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other

    def __str__(self):
        return str(self.value)

    def decrypt(self):
        return XOR.decrypt(self.value)


class EncryptedTextField(models.Field):

    def from_db_value(self, value, expression, context):
        return self.to_python(value)

    def to_python(self, value):
        if value is None or isinstance(value, EncryptedString):
            return value
        value = EncryptedString(value)
        return value

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        if isinstance(value, EncryptedString):
            return str(EncryptedString)
        value = XOR.encrypt(value)
        return value
