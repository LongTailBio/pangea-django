"""Test suite for experimental functions."""

import pandas as pd

from unittest import TestCase
from os.path import join, dirname
from os import environ

from pangea_api import (
    Knex,
    Sample,
    Organization,
    User,
)

PACKET_DIR = join(dirname(__file__), 'built_packet')
ENDPOINT = environ.get('PANGEA_API_TESTING_ENDPOINT', 'http://127.0.0.1:8000')
USERNAME = environ.get('PANGEA_API_TESTING_USERNAME', 'foo@bar.com')
PASSWORD = environ.get('PANGEA_API_TESTING_PASSWORD', 'Foobar22')


class TestPacketParser(TestCase):
    """Test suite for packet building."""

    def setUp(self):
        self.knex = Knex(ENDPOINT)
        self.user = User(self.knex, USERNAME, PASSWORD).register()

    def test_create_org(self):
        """Test that we can create a sample."""
        org = Organization(self.knex, 'my_client_test_org')
        org.create()
        self.assertTrue(org.uuid)
