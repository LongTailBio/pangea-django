
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.encrypted_fields import EncryptedString
from pangea.core.models import (
    PangeaUser,
    Organization,
    S3ApiKey,
    S3Bucket,
)

from .constants import (
    UPLOAD_TEST_FILENAME,
    UPLOAD_TEST_FILEPATH,
)


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
