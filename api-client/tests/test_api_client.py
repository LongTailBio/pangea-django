"""Test suite for experimental functions."""

from os import environ
from os.path import join, dirname
from requests.exceptions import HTTPError
from unittest import TestCase

from pangea_api import (
    Knex,
    Sample,
    Organization,
    User,
)

PACKET_DIR = join(dirname(__file__), 'built_packet')
ENDPOINT = environ.get('PANGEA_API_TESTING_ENDPOINT', 'http://127.0.0.1:8000')


class TestPacketParser(TestCase):
    """Test suite for packet building."""

    def setUp(self):
        self.knex = Knex(ENDPOINT)
        self.user = User(self.knex, 'foo@bar.com', 'Foobar22')
        try:
            self.user.register()
        except HTTPError:
            self.user.login()

    def test_create_org(self):
        """Test that we can create a sample."""
        org = Organization(self.knex, 'my_client_test_org')
        org.create()
        self.assertTrue(org.uuid)
