"""Test suite for Sample model."""
import os
from django.test import TestCase

from ..encrypted_fields import EncryptedString
from ..models import (
    Organization,
    S3ApiKey,
    S3Bucket,
    S3Provider,
)


class TestS3ApiKeyModel(TestCase):

    def test_encrypt_on_save(self):
        org = Organization.objects.create(name='Test Organization')
        bucket = S3Bucket.objects.create(
            organization=org,
            name='test_bucket',
            endpoint_url='https://sys.foobar.com',
        )
        key = S3ApiKey(
            bucket=bucket,
            description='KEY_01',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        key.save()
        self.assertTrue(key.uuid)
        retrieved = S3ApiKey.objects.get(pk=key.uuid)
        self.assertEqual(retrieved.public_key, 'my_public_key')
        self.assertNotEqual(retrieved.private_key, 'my_private_key')
        self.assertTrue(isinstance(retrieved.private_key, EncryptedString))
        self.assertEqual(retrieved.private_key.decrypt(), 'my_private_key')

    def test_get_presigned_url(self):
        pubkey = os.environ.get('PANGEA_S3_TESTER_PUBLIC_KEY', None)
        privkey = os.environ.get('PANGEA_S3_TESTER_PRIVATE_KEY', None)
        if not (pubkey and privkey):
            return  # Only run this test if the keys are available
        org = Organization.objects.create(name='Test Organization')
        bucket = S3Bucket.objects.create(
            organization=org,
            name='pangea.test.bucket',
            endpoint_url='https://s3.wasabisys.com',
        )
        key = S3ApiKey(
            bucket=bucket,
            description='KEY_01',
            public_key=pubkey,
            private_key=privkey,
        )
        key.save()
        retrieved = S3ApiKey.objects.get(pk=key.uuid)
        url = retrieved.presign_url(
            'https://s3.wasabisys.com',
            's3://pangea.test.bucket/my_private_s3_test_file.txt'
        )
        self.assertTrue(
            url.startswith('https://s3.wasabisys.com/pangea.test.bucket/my_private_s3_test_file.txt')
        )
        self.assertIn('AWSAccessKeyId=', url)
        self.assertIn('Signature=', url)
        self.assertIn('Expires=', url)


class TestS3Provider(TestCase):

    def test_encrypt_on_save(self):
        provider = S3Provider(
            name='a_storage_provider',
            s3_endpoint_url='https://s3.wasabisys.com',
            iam_endpoint_url='https://iam.wasabisys.com',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        provider.save()
        self.assertTrue(provider.uuid)
        retrieved = S3Provider.objects.get(pk=provider.uuid)
        self.assertEqual(retrieved.public_key, 'my_public_key')
        self.assertNotEqual(retrieved.private_key, 'my_private_key')
        self.assertTrue(isinstance(retrieved.private_key, EncryptedString))
        self.assertEqual(retrieved.private_key.decrypt(), 'my_private_key')

    def test_create_bucket(self):
        pubkey = None
        privkey = None
        """
        Do not run this test since it pollutes the bucket.

        To run it add an admin/root key pair.
        """
        if not (pubkey and privkey):
            return  # Only run this test if the keys are available
        provider = S3Provider(
            name='a_storage_provider',
            s3_endpoint_url='https://s3.wasabisys.com',
            iam_endpoint_url='https://iam.wasabisys.com',
            public_key=pubkey,
            private_key=privkey,
        )
        provider.save()
        org = Organization.objects.create(name='Test Organization UYDSHJG')
        group = org.create_sample_group(name='GRP_01 UYDSHJG')
        retrieved = S3Provider.objects.get(pk=provider.uuid)
        bucket, key = retrieved.create_bucket(group)
        self.assertTrue(bucket.uuid)
        self.assertTrue(bucket.name)
        self.assertTrue(key.uuid)
