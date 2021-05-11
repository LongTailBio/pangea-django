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
    SampleGroupWiki,
)

from .constants import (
    UPLOAD_TEST_FILENAME,
    UPLOAD_TEST_FILEPATH,
)


class SampleGroupTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.creds = ('user@domain.com', 'Foobar22')
        cls.user = PangeaUser.objects.create(email=cls.creds[0], password=cls.creds[1])

    def test_public_sample_group_read(self):
        """Ensure no login is required to read public group."""
        group = self.organization.create_sample_group(name='GRP_01 PUBLIC_GJYJ')
        url = reverse('sample-group-details', kwargs={'pk': group.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authorized_sample_group_read(self):
        """Ensure authorized user can read private sample group."""
        group = self.organization.create_sample_group(name='GRP_01 PRIVATE_GJYJ', is_public=False)
        url = reverse('sample-group-details', kwargs={'pk': group.uuid})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_guest_authorized_sample_group_read(self):
        """Ensure authorized user can read private sample group."""
        group = self.organization.create_sample_group(name='GRP_01 PRIVATE_ISNR', is_public=False)
        url = reverse('sample-group-details', kwargs={'pk': group.uuid})
        group.guest_users.add(self.user)
        group.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_login_sample_group_read(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        group = self.organization.create_sample_group(name='GRP_01 PRIVATE_GJYJ', is_public=False)
        url = reverse('sample-group-details', kwargs={'pk': group.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_sample_group_read(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        other_org = Organization.objects.create(name='Test Organization UYYGHJGHJGHJ')
        group = other_org.create_sample_group(name='GRP_01 PRIVATE_UYYGHJGHJGHJ', is_public=False)
        url = reverse('sample-group-details', kwargs={'pk': group.uuid})
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_login_sample_group_list(self):
        """Ensure 403 error is thrown if trying to illicitly read private group."""
        pub_group = self.organization.create_sample_group(
            name='GRP_01 PUBLIC_GJYJYIBSBN', is_public=True, is_library=True
        )
        other_org = Organization.objects.create(name='Test Organization GJYJYIBSBN')
        priv_group = other_org.create_sample_group(
            name='GRP_01 PRIVATE_GJYJYIBSBN', is_public=False, is_library=True
        )
        url = reverse('sample-group-create')
        response = self.client.get(url, format='json')
        names = {el['name'] for el in response.data['results']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(pub_group.name, names)
        self.assertNotIn(priv_group.name, names)

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

    def test_create_sample_group_with_descriptions(self):
        """Ensure authorized user can create sample group."""
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)

        url = reverse('sample-group-create')
        data = {
            'name': 'Test Sample Group',
            'organization': self.organization.pk,
            'description': 'short description',
            'long_description': 'long_description',
            'metadata': {'a': 1, 'b': 'foo'},
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleGroup.objects.count(), 1)
        self.assertEqual(SampleGroup.objects.get().name, 'Test Sample Group')

    def test_get_sample_group_manifest(self):
        """Ensure authorized user can create sample group."""
        group = self.organization.create_sample_group(
            name='GRP_01 IUHDJSFGKJL',
            is_public=True,
            is_library=True,
        )
        gar = group.create_analysis_result(module_name='module_foobar')
        gar.create_field(name='my_group_field_name', stored_data={})
        sample = group.create_sample(name='SMPL_01 IUHDJSFGKJL')
        ar = sample.create_analysis_result(module_name='module_foobar')
        ar.create_field(name='my_sample_field_name', stored_data={})

        url = reverse('sample-group-manifest', kwargs={'pk': group.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_sample_group_manifest_with_token_as_param(self):
        """Ensure authorized user can get a manifest using the tokan as a param."""
        group = self.organization.create_sample_group(
            name='GRP_01 TUYFNMJWHT',
            is_public=False,
            is_library=True,
        )
        gar = group.create_analysis_result(module_name='module_foobar')
        gar.create_field(name='my_group_field_name', stored_data={})
        sample = group.create_sample(name='SMPL_01 TUYFNMJWHT')
        ar = sample.create_analysis_result(module_name='module_foobar')
        ar.create_field(name='my_sample_field_name', stored_data={})

        # get the token
        register_url = '/api/auth/users/'
        body = {'email': 'foo@bar.biz', 'password': 'bizzbuzzbizzbar'}
        response = self.client.post(register_url, body, format='json')
        myuser = PangeaUser.objects.get(email=body['email'])
        self.organization.users.add(myuser)
        token_url = reverse('login')
        response = self.client.post(token_url, body, format='json')
        token = response.json()['auth_token']

        # check we're not logged in
        url = reverse('sample-group-manifest', kwargs={'pk': group.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check not just any old token works
        url = reverse('sample-group-manifest', kwargs={'pk': group.uuid})
        url += f'?token=FOOBAR'
        response = self.client.get(url, format='json')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        url = reverse('sample-group-manifest', kwargs={'pk': group.uuid})
        url += f'?token={token}'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauth_get_sample_group_manifest(self):
        """Ensure authorized user can create sample group."""
        group = self.organization.create_sample_group(
            name='GRP_01 TJFDWOTDSN',
            is_public=False,
            is_library=True,
        )
        gar = group.create_analysis_result(module_name='module_foobar')
        gar.create_field(name='my_group_field_name', stored_data={})
        sample = group.create_sample(name='SMPL_01 TJFDWOTDSN')
        ar = sample.create_analysis_result(module_name='module_foobar')
        ar.create_field(name='my_sample_field_name', stored_data={})

        url = reverse('sample-group-manifest', kwargs={'pk': group.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_sample_group_metadata_with_token_as_param(self):
        """Ensure authorized user can get a manifest using the tokan as a param."""
        group = self.organization.create_sample_group(
            name='GRP_01 TYAMWWTDSWNSFH',
            is_public=False,
            is_library=True,
        )
        group.create_sample(name='SMPL_01 TYAMWWTDSWNSFH', metadata={'a': 1, 'b': 1})
        group.create_sample(name='SMPL_02 TYAMWWTDSWNSFH', metadata={'a': 2, 'b': 1})

        # get the token
        register_url = '/api/auth/users/'
        body = {'email': 'TYAMWWTDSWNSFH@bar.biz', 'password': 'bizzbuzzbizzbar'}
        response = self.client.post(register_url, body, format='json')
        myuser = PangeaUser.objects.get(email=body['email'])
        self.organization.users.add(myuser)
        token_url = reverse('login')
        response = self.client.post(token_url, body, format='json')
        token = response.json()['auth_token']

        # check we're not logged in
        url = reverse('sample-group-metadata', kwargs={'pk': group.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check not just any old token works
        url = reverse('sample-group-metadata', kwargs={'pk': group.uuid})
        url += f'?token=FOOBAR'
        response = self.client.get(url, format='json')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        url = reverse('sample-group-metadata', kwargs={'pk': group.uuid})
        url += f'?token={token}'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_tarball(self):
        group = self.organization.create_sample_group(
            name='GRP_01 TFHJADGSDFTGH',
            is_public=True,
            is_library=True,
        )
        s1 = group.create_sample(name='SMPL_01 TFHJADGSDFTGH')
        s2 = group.create_sample(name='SMPL_02 TFHJADGSDFTGH')
        ar1 = s1.create_analysis_result(module_name='foo')
        ar2 = s2.create_analysis_result(module_name='foo')
        arf1 = ar1.create_field(name='bar', stored_data={'a': 1, 'b': 1})
        arf2 = ar2.create_field(name='bar', stored_data={'a': 2, 'b': 1})
        url = reverse('sample-group-download', kwargs={'pk': group.uuid, 'module_name': 'foo'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SampleGroupMembershipTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.org_user = PangeaUser.objects.create(email='org_user@domain.com', password='Foobar22')
        cls.anon_user = PangeaUser.objects.create(email='anon_user@domain.com', password='Foobar22')
        cls.organization.users.add(cls.org_user)
        cls.sample_library = cls.organization.create_sample_group(name='Test Library', is_library=True)
        cls.sample_group = cls.organization.create_sample_group(name='Test Group', is_library=False)
        cls.sample_library = cls.sample_library.library
        cls.sample = Sample.objects.create(name='Test Sample', library=cls.sample_library, metadata={'a': 'b'})
        cls.sample2 = Sample.objects.create(name='Test Sample 2', library=cls.sample_library, metadata={'a': 2})
        cls.sample3 = Sample.objects.create(name='Test Sample 3', library=cls.sample_library)

    def test_unauthenticated_add_sample_to_group(self):
        url = reverse('sample-group-samples', kwargs={'group_pk': self.sample_group.pk})
        data = {'sample_uuid': self.sample.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        samples_queryset = Sample.objects.filter(sample_groups__pk=self.sample_group.pk)
        self.assertEqual(samples_queryset.count(), 0)

    def test_unauthorized_add_sample_to_group(self):
        self.client.force_authenticate(user=self.anon_user)
        url = reverse('sample-group-samples', kwargs={'group_pk': self.sample_group.pk})
        data = {'sample_uuid': self.sample.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        samples_queryset = Sample.objects.filter(sample_groups__pk=self.sample_group.pk)
        self.assertEqual(samples_queryset.count(), 0)

    def test_authorized_add_sample_to_group(self):
        self.client.force_authenticate(user=self.org_user)
        url = reverse('sample-group-samples', kwargs={'group_pk': self.sample_group.pk})
        data = {'sample_uuid': self.sample.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        samples_queryset = Sample.objects.filter(sample_groups__pk=self.sample_group.pk)
        self.assertEqual(samples_queryset.count(), 1)

    def test_authorized_multi_add_sample_to_group(self):
        self.client.force_authenticate(user=self.org_user)
        url = reverse('sample-group-samples', kwargs={'group_pk': self.sample_group.pk})
        data = {
            'sample_uuid': self.sample.pk,
            'sample_uuids': [self.sample2.pk, self.sample3.pk]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        samples_queryset = Sample.objects.filter(sample_groups__pk=self.sample_group.pk)
        self.assertEqual(samples_queryset.count(), 3)

    def test_authorized_remove_sample_from_group(self):
        self.client.force_authenticate(user=self.org_user)
        url = reverse('sample-group-samples', kwargs={'group_pk': self.sample_group.pk})
        data = {
            'sample_uuid': self.sample.pk,
            'sample_uuids': [self.sample2.pk, self.sample3.pk]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('sample-group-samples', kwargs={'group_pk': self.sample_group.pk})
        data = {
            'sample_uuid': self.sample.pk,
            'sample_uuids': [self.sample2.pk]
        }
        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        samples_queryset = Sample.objects.filter(sample_groups__pk=self.sample_group.pk)
        self.assertEqual(samples_queryset.count(), 1)

    def test_generate_sample_group_sample_metadata_schema(self):
        self.client.force_authenticate(user=self.org_user)
        self.sample_group.add_sample(self.sample)
        self.sample_group.add_sample(self.sample2)
        url = reverse('sample-group-generate-schema', kwargs={'pk': self.sample_group.pk})
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['schema'])

    def test_validate_sample_group_sample_metadata_schema(self):
        self.sample_group.add_sample(self.sample)
        self.sample_group.add_sample(self.sample2)
        self.sample_group.sample_metadata_schema = {'fields': [{"name": "a", "type": "number"}]}
        self.sample_group.save()
        url = reverse('sample-group-validate-schema', kwargs={'pk': self.sample_group.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stats']['errors'], 1)

    def test_get_sample_group_samples(self):
        self.sample_group.sample_set.add(self.sample)

        url = reverse('sample-group-samples', kwargs={'group_pk': self.sample_group.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('Test Sample', [sample['name'] for sample in response.data['results']])

    def test_get_sample_group_samples(self):
        self.sample_group.sample_set.add(self.sample)

        url = reverse('sample-group-sample-links', kwargs={'pk': self.sample_group.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('Test Sample', [sample['name'] for sample in response.data['links']])


class SampleGroupWikiTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.creds = ('user@domain.com', 'Foobar22')
        cls.user = PangeaUser.objects.create(email=cls.creds[0], password=cls.creds[1])
        cls.organization.users.add(cls.user)
        cls.grp = cls.organization.create_sample_group(name='Test Group', is_library=False)
        cls.grp_with_wiki = cls.organization.create_sample_group(name='Test Group with Wiki', is_library=False)
        SampleGroupWiki.create_wiki(cls.grp_with_wiki)

    def test_get_wiki(self):
        url = reverse('sample-group-wiki', kwargs={'pk': self.grp_with_wiki.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_wiki(self):
        url = reverse('sample-group-wiki', kwargs={'pk': self.grp.pk})
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'title',
            'text': 'body',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.grp.wiki)
        self.assertEqual(self.grp.wiki.wiki.pages.count(), 1)
        self.assertEqual(self.grp.wiki.wiki.home_page.title, 'title')

    def test_add_page(self):
        url = reverse('sample-group-wiki', kwargs={'pk': self.grp_with_wiki.pk})
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'title',
            'text': 'body',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.grp_with_wiki.wiki)
        self.assertEqual(self.grp_with_wiki.wiki.pages.count(), 2)

    def test_modify_page(self):
        url = reverse('sample-group-wiki', kwargs={'pk': self.grp_with_wiki.pk})
        self.client.force_authenticate(user=self.user)
        data = {
            'uuid': self.grp_with_wiki.wiki.wiki.home_page.uuid,
            'title': 'title 2',
            'text': 'body',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.grp_with_wiki.refresh_from_db()
        self.assertTrue(self.grp_with_wiki.wiki)
        self.assertEqual(self.grp_with_wiki.wiki.pages.count(), 1)
        self.assertEqual(self.grp_with_wiki.wiki.home_page.title, 'title 2')
