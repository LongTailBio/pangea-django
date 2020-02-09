from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.models import PangeaUser, Organization, SampleGroup


class OrganizationTests(APITestCase):

    def test_create_unauthed_organization(self):
        """Ensure 403 error is throw when trying to create organization if unauthed."""
        url = reverse('organization-create')
        data = {'name': 'Test Organization'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Organization.objects.count(), 0)

    def test_create_organization(self):
        """Ensure authenticated user can create organization."""
        user = PangeaUser.objects.create(email='user@domain.com',password='Foobar22')
        self.client.force_authenticate(user=user)

        url = reverse('organization-create')
        data = {'name': 'Test Organization'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organization.objects.count(), 1)
        self.assertEqual(Organization.objects.get().name, 'Test Organization')
        self.assertIn(user, Organization.objects.get().users.all())


class SampleGroupTests(APITestCase):

    def test_create_unauthenticated_sample_group(self):
        """Ensure 403 error is throw when trying to create sample group if unauthenticated."""
        organization = Organization.objects.create(name='Test Organization')
        url = reverse('sample-group-create')
        data = {'name': 'Test Sample Group', 'organization': organization.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SampleGroup.objects.count(), 0)

    def test_create_unauthorized_sample_group(self):
        """Ensure 403 error is throw when trying to create sample group if unauthorized."""
        user = PangeaUser.objects.create(email='user@domain.com',password='Foobar22')
        self.client.force_authenticate(user=user)

        organization = Organization.objects.create(name='Test Organization')
        url = reverse('sample-group-create')
        data = {'name': 'Test Sample Group', 'organization': organization.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SampleGroup.objects.count(), 0)

    def test_create_sample_group(self):
        """Ensure authorized user can create sample group."""
        organization = Organization.objects.create(name='Test Organization')
        user = PangeaUser.objects.create(email='user@domain.com',password='Foobar22')
        organization.users.add(user)
        self.client.force_authenticate(user=user)

        url = reverse('sample-group-create')
        data = {'name': 'Test Sample Group', 'organization': organization.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleGroup.objects.count(), 1)
        self.assertEqual(SampleGroup.objects.get().name, 'Test Sample Group')
