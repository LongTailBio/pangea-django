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


class SampleTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')

    def test_public_sample_read(self):
        """Ensure no login is required to read public group."""
        group = self.organization.create_sample_group(name='GRP_01 PUBLIC_YUDB', is_library=True)
        sample = group.create_sample(name='SMPL_01 YUDB')
        url = reverse('sample-details', kwargs={'pk': sample.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authorized_sample_read(self):
        """Ensure authorized user can read private sample group."""
        group = self.organization.create_sample_group(
            name='GRP_01 PRIVATE_TYVNV',
            is_public=False,
            is_library=True,
        )
        sample = group.create_sample(name='SMPL_01 YUDB')
        url = reverse('sample-details', kwargs={'pk': sample.uuid})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_login_sample_read(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        group = self.organization.create_sample_group(
            name='GRP_01 PRIVATE_UHHKJ',
            is_public=False,
            is_library=True,
        )
        sample = group.create_sample(name='SMPL_01 UHHKJ')
        url = reverse('sample-details', kwargs={'pk': sample.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_sample_read(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        other_org = Organization.objects.create(name='Test Organization JHGJHGH')
        group = other_org.create_sample_group(
            name='GRP_01 PRIVATE_JHGJHGH',
            is_public=False,
            is_library=True,
        )
        sample = group.create_sample(name='SMPL_01 JHGJHGH')
        url = reverse('sample-details', kwargs={'pk': sample.uuid})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_login_sample_list(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        pub_group = self.organization.create_sample_group(
            name='GRP_01 PUBLIC_RTJNDRPOF', is_public=True, is_library=True
        )
        pub_samp = pub_group.create_sample(name='SMPL PUBLIC_RTJNDRPOF')
        other_org = Organization.objects.create(name='Test Organization RTJNDRPOF')
        priv_group = other_org.create_sample_group(
            name='GRP_01 PRIVATE_RTJNDRPOF', is_public=False, is_library=True
        )
        priv_samp = priv_group.create_sample(name='SMPL PRIVATE_RTJNDRPOF')

        url = reverse('sample-create')
        response = self.client.get(url, format='json')
        names = {el['name'] for el in response.data['results']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(pub_samp.name, names)
        self.assertNotIn(priv_samp.name, names)

    def test_create_unauthenticated_sample(self):
        """Ensure 403 error is throw when trying to create sample if unauthenticated."""
        sample_library = self.organization.create_sample_group(name='Test Library', is_library=True)
        url = reverse('sample-create')
        data = {'name': 'Test Sample', 'library': sample_library.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Sample.objects.count(), 0)

    def test_create_unauthorized_sample(self):
        """Ensure 403 error is throw when trying to create sample group if unauthorized."""
        self.client.force_authenticate(user=self.user)

        sample_library = self.organization.create_sample_group(name='Test Library', is_library=True)
        url = reverse('sample-create')
        data = {'name': 'Test Sample', 'library': sample_library.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Sample.objects.count(), 0)

    def test_create_sample(self):
        """Ensure authorized user can create sample group."""
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)

        sample_library = self.organization.create_sample_group(name='Test Library', is_library=True)
        url = reverse('sample-create')
        data = {'name': 'Test Sample', 'library': sample_library.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sample.objects.count(), 1)
        self.assertEqual(Sample.objects.get().name, 'Test Sample')
        self.assertTrue(sample_library.sample_set.filter(pk=response.data.get('uuid')).exists())

    def test_modify_sample_library(self):
        """Ensure authorized user can move sample to another library."""
        group = self.organization.create_sample_group(
            name='GRP_01 KYDJAH',
            is_public=True,
            is_library=True,
        )
        sample = group.create_sample(name='SMPL_01 KYDJAH')
        sample_library = self.organization.create_sample_group(name='Test Library KYDJAH', is_library=True)

        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)

        url = reverse('sample-details', kwargs={'pk': sample.uuid})
        data = {'library': sample_library.pk}
        response = self.client.patch(url, data, format='json')

        sample = Sample.objects.get(pk=sample.uuid)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(sample.library.group.uuid, group.uuid)
        self.assertEqual(sample.library.group.uuid, sample_library.uuid)
        self.assertTrue(sample_library.sample_set.filter(pk=sample.uuid).exists())
        self.assertFalse(group.sample_set.filter(pk=sample.uuid).exists())

    def test_create_sample_with_description(self):
        """Ensure authorized user can create sample group."""
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)

        sample_library = self.organization.create_sample_group(name='Test Library', is_library=True)
        url = reverse('sample-create')
        data = {
            'name': 'Test Sample',
            'library': sample_library.pk,
            'description': 'a sample',
            'metadata': {'A': 1, 'B': 'foo'}
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sample.objects.count(), 1)
        self.assertEqual(Sample.objects.get().name, 'Test Sample')
        self.assertTrue(sample_library.sample_set.filter(pk=response.data.get('uuid')).exists())

    def test_get_sample_manifest(self):
        """Ensure authorized user can create sample group."""
        group = self.organization.create_sample_group(
            name='GRP_01 TUFHGGJHFD',
            is_public=True,
            is_library=True,
        )
        sample = group.create_sample(name='SMPL_01 TUFHGGJHFD')
        ar = sample.create_analysis_result(module_name='module_foobar')
        ar.create_field(name='my_sample_field_name', stored_data={})

        url = reverse('sample-manifest', kwargs={'pk': sample.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauth_get_sample_manifest(self):
        """Ensure authorized user can create sample group."""
        group = self.organization.create_sample_group(
            name='GRP_01 TDSFDHORUEI',
            is_public=False,
            is_library=True,
        )
        sample = group.create_sample(name='SMPL_01 TDSFDHORUEI')
        ar = sample.create_analysis_result(module_name='module_foobar')
        ar.create_field(name='my_sample_field_name', stored_data={})

        url = reverse('sample-manifest', kwargs={'pk': sample.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SampleMetadataTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.lib = cls.organization.create_sample_group(name='Test Library', is_library=True)
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')
        cls.organization.users.add(cls.user)

    def test_update_metadata(self):
        """Ensure authorized user can create sample group."""
        self.client.force_authenticate(user=self.user)

        data = {'name': 'Test Sample', 'library': self.lib.pk, 'metadata': {'foo': 1}}
        response = self.client.post(reverse('sample-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        sample_obj = Sample.objects.get()  # should only be one sample
        self.assertEqual(sample_obj.metadata['foo'], 1)

        data = {'metadata': {'foo': 2}}
        response = self.client.patch(
            reverse('sample-details', kwargs={'pk': sample_obj.uuid}),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sample_obj = Sample.objects.get()  # should only be one sample
        self.assertEqual(sample_obj.metadata['foo'], 2)

    def test_retrieve_metadata(self):
        self.client.force_authenticate(user=self.user)

        data = {'name': 'Test Sample GJKJH', 'library': self.lib.pk, 'metadata': {'bar': 1}}
        response = self.client.post(reverse('sample-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        sample_obj = Sample.objects.get()  # should only be one sample
        response = self.client.patch(
            reverse('sample-details', kwargs={'pk': sample_obj.uuid}),
            {'metadata': {'bar': 2}},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(
            reverse('sample-versioned-metadata', kwargs={'pk': sample_obj.uuid}),
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vm = response.data.get('versioned_metadata', [])
        self.assertTrue(vm)
        self.assertEqual(len(vm), 2)
