import os
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.encrypted_fields import EncryptedString
from pangea.core.models import (
    PangeaUser,
    Organization,
    S3ApiKey,
    SampleGroup,
    SampleLibrary,
    Sample,
    SampleGroupAnalysisResult,
    SampleAnalysisResult,
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
        cls.org_user = PangeaUser.objects.create(email='org_user@domain.com', password='Foobar22')
        cls.anon_user = PangeaUser.objects.create(email='anon_user@domain.com', password='Foobar22')
        cls.organization.users.add(cls.org_user)

    def test_authorized_s3apikey_read(self):
        """Ensure authorized user can read private sample group."""
        s3apikey = self.organization.create_s3apikey(
            description='KEY_01',
            endpoint_url='https://sys.foobar.com',
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
        s3apikey = self.organization.create_s3apikey(
            description='KEY_01',
            endpoint_url='https://sys.foobar.com',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        url = reverse('s3apikey-details', kwargs={'pk': s3apikey.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_s3apikey_read(self):
        """Ensure 403 error is thrown if trying to illicitly read s3apikey."""
        s3apikey = self.organization.create_s3apikey(
            description='KEY_01',
            endpoint_url='https://sys.foobar.com',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        url = reverse('s3apikey-details', kwargs={'pk': s3apikey.uuid})
        self.client.force_authenticate(user=self.anon_user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authorized_s3apikey_list(self):
        """Ensure 403 error is thrown if trying to illicitly read api keys."""
        s3apikey = self.organization.create_s3apikey(
            description='KEY_01',
            endpoint_url='https://sys.foobar.com',
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
        s3apikey = self.organization.create_s3apikey(
            description='KEY_01',
            endpoint_url='https://sys.foobar.com',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        url = reverse('s3apikey-create')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_s3apikey_list(self):
        """Ensure 403 error is thrown if trying to illicitly read api keys."""
        s3apikey = self.organization.create_s3apikey(
            description='KEY_01',
            endpoint_url='https://sys.foobar.com',
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
            'endpoint_url': 'https://sys.foobar.com',
            'public_key': 'my_public_key',
            'private_key': 'my_private_key',
            'organization': self.organization.pk,
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
            'endpoint_url': 'https://sys.foobar.com',
            'public_key': 'my_public_key',
            'private_key': 'my_private_key',
            'organization': self.organization.pk,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_in_org_create_key(self):
        self.client.force_authenticate(user=self.anon_user)
        url = reverse('s3apikey-create')
        data = {
            'endpoint_url': 'https://sys.foobar.com',
            'public_key': 'my_public_key',
            'private_key': 'my_private_key',
            'organization': self.organization.pk,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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
        cls.sample = Sample.objects.create(name='Test Sample', library=cls.sample_library)

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

    def test_get_sample_group_samples(self):
        self.sample_group.sample_set.add(self.sample)

        url = reverse('sample-group-samples', kwargs={'group_pk': self.sample_group.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('Test Sample', [sample['name'] for sample in response.data['results']])


class AnalysisResultTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.user = PangeaUser.objects.create(email='user@domain.com',password='Foobar22')
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
        self.organization.create_s3apikey(
            description='KEY_01',
            endpoint_url='https://s3.wasabisys.com',
            public_key=pubkey,
            private_key=privkey,
        )
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
