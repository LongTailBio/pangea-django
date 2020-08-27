import os
import datetime
import requests

from boto3 import Session
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.models import (
    PangeaUser,
    Organization,
    Sample,
    SampleGroupAnalysisResult,
    SampleAnalysisResult,
)

from .constants import (
    UPLOAD_TEST_FILENAME,
    UPLOAD_TEST_FILEPATH,
    MULTIPART_UPLOAD_TEST_FILENAME,
    MULTIPART_UPLOAD_TEST_FILEPATH,
)


class AnalysisResultTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')
        cls.organization.users.add(cls.user)
        cls.sample_group = cls.organization.create_sample_group(name='Test Library', is_library=True)
        cls.sample_library = cls.sample_group.library
        cls.sample = Sample.objects.create(name='Test Sample', library=cls.sample_library)

    def test_public_sample_analysis_result_read(self):
        """Ensure no login is required to read public group."""
        group = self.organization.create_sample_group(name='GRP_01 PUBLIC_YUDB', is_library=True)
        sample = group.create_sample(name='SMPL_01 YUDB')
        ar = sample.create_analysis_result(module_name='module_foobar')
        url = reverse('sample-ars-details', kwargs={'pk': ar.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authorized_sample_analysis_result_read(self):
        """Ensure authorized user can read private sample group."""
        group = self.organization.create_sample_group(
            name='GRP_01 PRIVATE_TYVNV',
            is_public=False,
            is_library=True,
        )
        sample = group.create_sample(name='SMPL_01 YUDB')
        ar = sample.create_analysis_result(module_name='module_foobar')
        url = reverse('sample-ars-details', kwargs={'pk': ar.uuid})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_login_sample_analysis_result_read(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        group = self.organization.create_sample_group(
            name='GRP_01 PRIVATE_UHHKJ',
            is_public=False,
            is_library=True,
        )
        sample = group.create_sample(name='SMPL_01 UHHKJ')
        ar = sample.create_analysis_result(module_name='module_foobar')
        url = reverse('sample-ars-details', kwargs={'pk': ar.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_sample_analysis_result_read(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        other_org = Organization.objects.create(name='Test Organization JHGJHGH')
        group = other_org.create_sample_group(
            name='GRP_01 PRIVATE_JHGJHGH',
            is_public=False,
            is_library=True,
        )
        sample = group.create_sample(name='SMPL_01 JHGJHGH')
        ar = sample.create_analysis_result(module_name='module_foobar')
        url = reverse('sample-ars-details', kwargs={'pk': ar.uuid})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_login_sample_analysis_result_list(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        pub_group = self.organization.create_sample_group(
            name='GRP_01 PUBLIC_RTJNDRPOF', is_public=True, is_library=True
        )
        pub_samp = pub_group.create_sample(name='SMPL PUBLIC_RTJNDRPOF')
        pub_ar = pub_samp.create_analysis_result(module_name='module_foobar')
        other_org = Organization.objects.create(name='Test Organization RTJNDRPOF')
        priv_group = other_org.create_sample_group(
            name='GRP_01 PRIVATE_RTJNDRPOF', is_public=False, is_library=True
        )
        priv_samp = priv_group.create_sample(name='SMPL PRIVATE_RTJNDRPOF')
        priv_ar = pub_samp.create_analysis_result(module_name='module_foobar')
        url = reverse('sample-ars-create')
        response = self.client.get(url, format='json')
        names = {el['sample_obj']['name'] for el in response.data['results']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(pub_samp.name, names)
        self.assertNotIn(priv_samp.name, names)

    def test_create_sample_group_analysis_result(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('sample-group-ars-create')
        data = {'module_name': 'taxa', 'sample_group': self.sample_group.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleGroupAnalysisResult.objects.count(), 1)
        self.assertEqual(SampleGroupAnalysisResult.objects.get().sample_group, self.sample_group)
        self.assertEqual(SampleGroupAnalysisResult.objects.get().module_name, 'taxa')

    def test_create_sample_analysis_result(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('sample-ars-create')
        data = {'module_name': 'taxa', 'sample': self.sample.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleAnalysisResult.objects.count(), 1)
        self.assertEqual(SampleAnalysisResult.objects.get().sample, self.sample)
        self.assertEqual(SampleAnalysisResult.objects.get().module_name, 'taxa')

    def _setup_upload_presign(self, filename, stance=None, n_parts=1):
        pubkey = os.environ.get('PANGEA_S3_TESTER_PUBLIC_KEY', None)
        privkey = os.environ.get('PANGEA_S3_TESTER_PRIVATE_KEY', None)
        if not (pubkey and privkey):
            return  # Only run this test if the keys are available
        field = self.sample.create_analysis_result(
            module_name='test_file',
        ).create_field(name='file', stored_data={})
        self.organization.users.add(self.user)
        bucket = self.organization.create_s3bucket(
            endpoint_url='https://s3.wasabisys.com',
            name="pangea.test.bucket",
        )
        bucket.create_s3apikey(
            description='KEY_01',
            public_key=pubkey,
            private_key=privkey,
        )
        self.sample_group.add_s3_bucket(bucket)
        url = reverse('sample-ar-fields-get-upload-url', kwargs={'pk': field.uuid})
        self.client.force_authenticate(user=self.user)
        blob = {'filename': filename, 'n_parts': n_parts}
        if stance:
            blob['stance'] = stance
        response = self.client.post(url, blob, format='json')
        return response, field

    def test_get_multipart_upload_url(self):
        response, field = self._setup_upload_presign('my_test_file.foo', stance='upload-multipart', n_parts=2)
        self.assertEqual(2, len(response.data['urls']))

    def test_use_multipart_upload_url(self, max_size=5 * 1024 * 1024):
        file_size = os.path.getsize(MULTIPART_UPLOAD_TEST_FILEPATH)
        n_parts = int(file_size / max_size) + 1
        response, field = self._setup_upload_presign(
            'my_multipart_upload_test_file.txt',
            stance='upload-multipart',
            n_parts=n_parts
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parts = []
        with open(MULTIPART_UPLOAD_TEST_FILEPATH, 'rb') as f:
            for num, url in enumerate(response.data['urls']):
                file_data = f.read(max_size)
                http_response = requests.put(url, data=file_data)
                parts.append({
                    'ETag': http_response.headers['ETag'],
                    'PartNumber': num + 1
                })
                self.assertEqual(http_response.status_code, status.HTTP_200_OK)
        url = reverse('sample-ar-fields-get-upload-complete-url', kwargs={'pk': field.uuid})
        response = self.client.post(
            url,
            {'parts': parts, 'upload_id': response.data['upload_id']},
            format='json'
        )
        self.assertEqual(http_response.status_code, status.HTTP_200_OK)

    def test_get_upload_url(self):
        response, field = self._setup_upload_presign('my_test_file.foo')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['url'], 'https://s3.wasabisys.com/pangea.test.bucket')
        self.assertEqual(response.data['fields']['key'], 'pangea/Test Library/samples/Test Sample/my_test_file.foo')
        for key in ['AWSAccessKeyId', 'policy', 'signature']:
            self.assertIn(key, response.data['fields'])
        field.refresh_from_db()
        self.assertEqual(field.field_type, 's3')
        self.assertEqual(field.stored_data['uri'], 's3://pangea.test.bucket/pangea/Test Library/samples/Test Sample/my_test_file.foo')

    def test_use_upload_url(self):
        response, field = self._setup_upload_presign(UPLOAD_TEST_FILENAME)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with open(UPLOAD_TEST_FILEPATH, 'w') as f:
            f.write(datetime.datetime.now().isoformat())
        with open(UPLOAD_TEST_FILEPATH, 'rb') as f:
            files = {'file': (response.data['fields']['key'], f)}
            http_response = requests.post(response.data['url'], data=response.data['fields'], files=files)
        self.assertEqual(http_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_presign_s3_url_in_sample_ar_field(self):
        pubkey = os.environ.get('PANGEA_S3_TESTER_PUBLIC_KEY', None)
        privkey = os.environ.get('PANGEA_S3_TESTER_PRIVATE_KEY', None)
        if not (pubkey and privkey):
            return  # Only run this test if the keys are available
        field = self.sample.create_analysis_result(
            module_name='test_file',
        ).create_field(
            name='file',
            stored_data={
                '__type__': 's3',
                'endpoint_url': 'https://s3.wasabisys.com',
                'uri': 's3://pangea.test.bucket/my_private_s3_test_file.txt',
            }
        )
        self.organization.users.add(self.user)
        bucket = self.organization.create_s3bucket(
            endpoint_url='https://s3.wasabisys.com',
            name="pangea.test.bucket",
        )
        bucket.create_s3apikey(
            description='KEY_01',
            public_key=pubkey,
            private_key=privkey,
        )
        self.sample_group.add_s3_bucket(bucket)
        url = reverse('sample-ar-fields-details', kwargs={'pk': field.uuid})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['stored_data']
        self.assertIn('presigned_url', data)
        url = data['presigned_url']
        self.assertTrue(
            url.startswith('https://s3.wasabisys.com/pangea.test.bucket/my_private_s3_test_file.txt')
        )
        self.assertIn('AWSAccessKeyId=', url)
        self.assertIn('Signature=', url)
        self.assertIn('Expires=', url)

    def test_no_presign_s3_url_in_sample_ar_field(self):
        pubkey = os.environ.get('PANGEA_S3_TESTER_PUBLIC_KEY', None)
        privkey = os.environ.get('PANGEA_S3_TESTER_PRIVATE_KEY', None)
        if not (pubkey and privkey):
            return  # Only run this test if the keys are available
        field = self.sample.create_analysis_result(
            module_name='test_file',
        ).create_field(
            name='file',
            stored_data={
                '__type__': 's3',
                'endpoint_url': 'https://s3.wasabisys.com',
                'uri': 's3://pangea.test.bucket/my_private_s3_test_file.txt',
            }
        )
        self.organization.users.add(self.user)
        url = reverse('sample-ar-fields-details', kwargs={'pk': field.uuid})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['stored_data']
        self.assertNotIn('presigned_url', data)
