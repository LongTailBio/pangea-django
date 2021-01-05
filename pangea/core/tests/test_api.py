import os
import datetime
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.encrypted_fields import EncryptedString
from pangea.core.models import (
    PangeaUser,
    Organization,
    Project,
    S3ApiKey,
    S3Bucket,
    SampleGroup,
    SampleLibrary,
    Sample,
    SampleGroupAnalysisResult,
    SampleAnalysisResult,
)

from .constants import (
    UPLOAD_TEST_FILENAME,
    UPLOAD_TEST_FILEPATH,
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


class S3ApiKeyTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.bucket = cls.organization.create_s3bucket(
            endpoint_url='https://sys.foobar.com',
            name="test_bucket",
        )
        cls.org_user = PangeaUser.objects.create(email='org_user@domain.com', password='Foobar22')
        cls.anon_user = PangeaUser.objects.create(email='anon_user@domain.com', password='Foobar22')
        cls.organization.users.add(cls.org_user)

    def test_authorized_s3apikey_read(self):
        """Ensure authorized user can read private sample group."""
        s3apikey = self.bucket.create_s3apikey(
            description='KEY_01',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        url = reverse('s3apikey-details', kwargs={'pk': s3apikey.uuid})
        self.client.force_authenticate(user=self.org_user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('public_key', response.data)
        self.assertNotIn('private_key', response.data)

    def test_no_login_s3apikey_read(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        s3apikey = self.bucket.create_s3apikey(
            description='KEY_01',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        url = reverse('s3apikey-details', kwargs={'pk': s3apikey.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_s3apikey_read(self):
        """Ensure 403 error is thrown if trying to illicitly read s3apikey."""
        s3apikey = self.bucket.create_s3apikey(
            description='KEY_01',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        url = reverse('s3apikey-details', kwargs={'pk': s3apikey.uuid})
        self.client.force_authenticate(user=self.anon_user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authorized_s3apikey_list(self):
        """Ensure 403 error is thrown if trying to illicitly read api keys."""
        s3apikey = self.bucket.create_s3apikey(
            description='KEY_01',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        url = reverse('s3apikey-create')
        self.client.force_authenticate(user=self.org_user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_no_login_s3apikey_list(self):
        """Ensure 403 error is thrown if trying to illicitly read api keys."""
        s3apikey = self.bucket.create_s3apikey(
            description='KEY_01',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        url = reverse('s3apikey-create')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_s3apikey_list(self):
        """Ensure 403 error is thrown if trying to illicitly read api keys."""
        s3apikey = self.bucket.create_s3apikey(
            description='KEY_01',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        url = reverse('s3apikey-create')
        self.client.force_authenticate(user=self.anon_user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_key(self):
        self.client.force_authenticate(user=self.org_user)

        url = reverse('s3apikey-create')
        data = {
            'public_key': 'my_public_key',
            'private_key': 'my_private_key',
            'bucket': self.bucket.pk,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(S3ApiKey.objects.count(), 1)
        self.assertEqual(S3ApiKey.objects.get().public_key, 'my_public_key')
        # Test the private-key's value by accessing the model directly
        retrieved = S3ApiKey.objects.get(pk=response.data['uuid'])
        self.assertEqual(retrieved.public_key, 'my_public_key')
        self.assertNotEqual(retrieved.private_key, 'my_private_key')
        self.assertTrue(isinstance(retrieved.private_key, EncryptedString))
        self.assertEqual(retrieved.private_key.decrypt(), 'my_private_key')

    def test_unauth_create_key(self):
        url = reverse('s3apikey-create')
        data = {
            'public_key': 'my_public_key',
            'private_key': 'my_private_key',
            'bucket': self.bucket.pk,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_in_org_create_key(self):
        self.client.force_authenticate(user=self.anon_user)
        url = reverse('s3apikey-create')
        data = {
            'public_key': 'my_public_key',
            'private_key': 'my_private_key',
            'bucket': self.bucket.pk,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class S3BucketTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.org_user = PangeaUser.objects.create(email='org_user@domain.com', password='Foobar22')
        cls.anon_user = PangeaUser.objects.create(email='anon_user@domain.com', password='Foobar22')
        cls.organization.users.add(cls.org_user)

    def test_authorized_s3bucket_read(self):
        """Ensure authorized user can read private bucket."""
        bucket = self.organization.create_s3bucket(
            endpoint_url='https://sys.foobar.com',
            name="test_bucket",
        )
        url = reverse('s3bucket-details', kwargs={'pk': bucket.uuid})
        self.client.force_authenticate(user=self.org_user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('endpoint_url', response.data)
        self.assertIn('name', response.data)

    def test_authorized_s3bucket_list(self):
        """Ensure 403 error is thrown if trying to illicitly read api keys."""
        bucket = self.organization.create_s3bucket(
            endpoint_url='https://sys.foobar.com',
            name="test_bucket",
        )
        url = reverse('s3bucket-create')
        self.client.force_authenticate(user=self.org_user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_no_login_s3bucket_list(self):
        """Ensure 403 error is thrown if trying to illicitly read api keys."""
        bucket = self.organization.create_s3bucket(
            endpoint_url='https://sys.foobar.com',
            name="test_bucket",
        )
        url = reverse('s3bucket-create')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_s3bucket_list(self):
        """Ensure 403 error is thrown if trying to illicitly read api keys."""
        bucket = self.organization.create_s3bucket(
            endpoint_url='https://sys.foobar.com',
            name="test_bucket",
        )
        url = reverse('s3bucket-create')
        self.client.force_authenticate(user=self.anon_user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_create_bucket(self):
        self.client.force_authenticate(user=self.org_user)
        url = reverse('s3bucket-create')
        data = {
            'endpoint_url': 'https://sys.foobar.com',
            'name': "test_bucket",
            'organization': self.organization.pk,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(S3Bucket.objects.count(), 1)
        self.assertEqual(S3Bucket.objects.get().endpoint_url, 'https://sys.foobar.com')
        # Test the private-key's value by accessing the model directly
        retrieved = S3Bucket.objects.get(pk=response.data['uuid'])
        self.assertEqual(retrieved.endpoint_url, 'https://sys.foobar.com')
        self.assertEqual(retrieved.name, 'test_bucket')


class OrganizationMembershipTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.org_user = PangeaUser.objects.create(email='org_user@domain.com', password='Foobar22')
        cls.anon_user = PangeaUser.objects.create(email='anon_user@domain.com', password='Foobar22')
        cls.target_user = PangeaUser.objects.create(email='target_user@domain.com', password='Foobar22')
        cls.organization.users.add(cls.org_user)

    def add_target_user(self):
        url = reverse('organization-users', kwargs={'organization_pk': self.organization.pk})
        data = {'user': self.target_user.pk}
        response = self.client.post(url, data, format='json')
        return response

    def test_unauthenticated_add_user_to_organization(self):
        response = self.add_target_user()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        organizations_queryset = Organization.objects.filter(users__pk=self.target_user.pk)
        self.assertEqual(organizations_queryset.count(), 0)

    def test_unauthorized_add_user_to_organization(self):
        self.client.force_authenticate(user=self.anon_user)
        response = self.add_target_user()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        organizations_queryset = Organization.objects.filter(users__pk=self.target_user.pk)
        self.assertEqual(organizations_queryset.count(), 0)

    def test_authorized_add_user_to_organization(self):
        self.client.force_authenticate(user=self.org_user)
        response = self.add_target_user()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        organizations_queryset = Organization.objects.filter(users__pk=self.target_user.pk)
        self.assertEqual(organizations_queryset.count(), 1)

    def test_get_organization_users(self):
        self.organization.users.add(self.target_user)

        url = reverse('organization-users', kwargs={'organization_pk': self.organization.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertIn('target_user@domain.com', [user['email'] for user in response.data['results']])


class ProjectTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.creds = ('user@domain.com', 'Foobar22')
        cls.user = PangeaUser.objects.create(email=cls.creds[0], password=cls.creds[1])
        cls.organization.users.add(cls.user)
        cls.grp1 = cls.organization.create_sample_group(name='GRP_01', is_library=True)
        cls.grp2 = cls.organization.create_sample_group(name='GRP_02', is_public=False)

    def test_public_project_read(self):
        """Ensure no login is required to read public group."""
        proj = self.organization.create_project(name='PROJ_01 UYDSGH')
        proj.add_sample_group(self.grp1)
        url = reverse('project-details', kwargs={'pk': proj.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authorized_project_read(self):
        """Ensure authorized user can read private sample group."""
        proj = self.organization.create_project(name='PROJ_01 SRHJTR')
        proj.add_sample_group(self.grp2)
        url = reverse('project-details', kwargs={'pk': proj.uuid})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_login_project_read(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        proj = self.organization.create_project(name='PROJ_01 RETG')
        proj.add_sample_group(self.grp2)
        url = reverse('project-details', kwargs={'pk': proj.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_project_read(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        other_org = Organization.objects.create(name='Test Organization IRJHFJSAH')
        group = other_org.create_sample_group(name='GRP_01 PRIVATE_IRJHFJSAH', is_public=False)
        proj = other_org.create_project(name='PROJ_01 IRJHFJSAH')
        proj.add_sample_group(group)
        url = reverse('project-details', kwargs={'pk': proj.uuid})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_project(self):
        """Ensure authorized user can create sample group."""
        self.client.force_authenticate(user=self.user)

        url = reverse('project-create')
        data = {'name': 'Test Project', 'organization': self.organization.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().name, 'Test Project')

    def test_add_group_to_project(self):
        proj = self.organization.create_project(name='PROJ_01 SRHJTR')
        url = reverse('project-sample-groups', kwargs={'project_pk': proj.uuid})
        self.client.force_authenticate(user=self.user)

        data = {'sample_group_uuid': self.grp1.uuid}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
