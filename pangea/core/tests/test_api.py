from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.models import (
    PangeaUser,
    Organization,
    SampleGroup,
    SampleLibrary,
)


class OrganizationTests(APITestCase):

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


class SampleGroupTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')

    def test_create_unauthenticated_sample_group(self):
        """Ensure 403 error is throw when trying to create sample group if unauthenticated."""
        url = reverse('sample-group-create')
        data = {'name': 'Test Sample Group', 'organization': self.organization.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SampleGroup.objects.count(), 0)

    def test_create_unauthorized_sample_group(self):
        """Ensure 403 error is throw when trying to create sample group if unauthorized."""
        self.client.force_authenticate(user=self.user)

        url = reverse('sample-group-create')
        data = {'name': 'Test Sample Group', 'organization': self.organization.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SampleGroup.objects.count(), 0)

    def test_create_sample_group(self):
        """Ensure authorized user can create sample group."""
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)

        url = reverse('sample-group-create')
        data = {'name': 'Test Sample Group', 'organization': self.organization.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleGroup.objects.count(), 1)
        self.assertEqual(SampleGroup.objects.get().name, 'Test Sample Group')
