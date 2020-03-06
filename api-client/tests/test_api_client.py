import os
import sys

# Setup environ
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pangea.settings")

# Setup django
import django
django.setup()

from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.models import (
    PangeaUser,
    Organization,
    SampleGroup,
    SampleLibrary,
    Sample,
    SampleGroupAnalysisResult,
    SampleAnalysisResult,
)

from pangea_api_client


class ApiClientTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')

    def test_create_unauthed_organization(self):
        """Ensure 403 error is throw when trying to create organization if unauthed."""
        url = reverse('organization-create')
        data = {'name': 'Test Organization'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Organization.objects.count(), 0)

    def test_create_organization(self):
        """Ensure authenticated user can create organization."""
        self.client.force_authenticate(user=self.user)

        url = reverse('organization-create')
        data = {'name': 'Test Organization'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organization.objects.count(), 1)
        self.assertEqual(Organization.objects.get().name, 'Test Organization')
        self.assertIn(self.user, Organization.objects.get().users.all())
