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
    Pipeline,
    PipelineModule,
    OrganizationWiki,
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


class OrganizationWikiTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        
        cls.creds = ('user@domain.com', 'Foobar22')
        cls.user = PangeaUser.objects.create(email=cls.creds[0], password=cls.creds[1])
        cls.org = Organization.objects.create(name='Test Organization')
        cls.org.users.add(cls.user)

        cls.org_with_wiki = Organization.objects.create(name='Test Organization with Wiki')
        cls.org_with_wiki.users.add(cls.user)
        OrganizationWiki.create_wiki(cls.org_with_wiki)

    def test_get_wiki(self):
        url = reverse('organization-wiki', kwargs={'pk': self.org_with_wiki.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_new_wiki(self):
        url = reverse('organization-wiki', kwargs={'pk': self.org.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_page(self):
        url = reverse('organization-wiki', kwargs={'pk': self.org_with_wiki.pk})
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'title',
            'text': 'body',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.org_with_wiki.wiki)
        self.assertEqual(self.org_with_wiki.wiki.pages.count(), 2)

    def test_modify_page(self):
        url = reverse('organization-wiki', kwargs={'pk': self.org_with_wiki.pk})
        self.client.force_authenticate(user=self.user)
        data = {
            'uuid': self.org_with_wiki.wiki.home_page.uuid,
            'title': 'title 2',
            'text': 'body',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.org_with_wiki.refresh_from_db()
        self.assertTrue(self.org_with_wiki.wiki)
        self.assertEqual(self.org_with_wiki.wiki.pages.count(), 1)
        self.assertEqual(self.org_with_wiki.wiki.home_page.title, 'title 2')


class PangeaUserTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.org_user = PangeaUser.objects.create(email='org_user@domain.com', password='Foobar22')
        cls.anon_user = PangeaUser.objects.create(email='anon_user@domain.com', password='Foobar22')
        cls.target_user = PangeaUser.objects.create(email='target_user@domain.com', password='Foobar22')
        cls.organization.users.add(cls.org_user)

    def test_list_pangea_users(self):
        url = reverse('pangea-user-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_pangea_user(self):
        url = reverse('pangea-user-details', kwargs={'uuid': self.org_user.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'org_user@domain.com')
        self.assertEqual(len(response.data['organization_objs']), 1)
        self.assertEqual(response.data['organization_objs'][0]['uuid'], self.organization.uuid)

    def test_get_pangea_user_by_id(self):
        url = reverse('pangea-user-id-details', kwargs={'user_id': self.org_user.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'org_user@domain.com')
        self.assertEqual(len(response.data['organization_objs']), 1)
        self.assertEqual(response.data['organization_objs'][0]['uuid'], self.organization.uuid)

    def test_get_current_pangea_user(self):
        url = reverse('pangea-user-me-details')
        self.client.force_authenticate(user=self.target_user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'target_user@domain.com')

    def test_set_pangea_user_name(self):
        url = reverse('pangea-user-details', kwargs={'uuid': self.target_user.uuid})
        self.client.force_authenticate(user=self.target_user)
        response = self.client.patch(url, {'name': 'Pooter Bilbo'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.name, 'Pooter Bilbo')

    def test_unauthorized_set_pangea_user_name(self):
        url = reverse('pangea-user-details', kwargs={'uuid': self.target_user.uuid})
        response = self.client.patch(url, {'name': 'Booter Pilbo'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.target_user.refresh_from_db()
        self.assertNotEqual(self.target_user.name, 'Booter Pilbo')


class PipelineTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.pipeline = Pipeline.objects.create(name='Test Pipeline')
        cls.module = cls.pipeline.create_module(name='Test Module', version='vTEST')
        cls.creds = ('user@domain.com', 'Foobar22')
        cls.user = PangeaUser.objects.create(email=cls.creds[0], password=cls.creds[1])

    def test_pipeline_read(self):
        """Test retireve pipeline."""
        url = reverse('pipeline-details', kwargs={'pk': self.pipeline.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pipeline_read_by_name(self):
        """Test retireve pipeline."""
        url = reverse('pipeline-name-details', kwargs={'name': self.pipeline.name})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pipeline_module_read(self):
        """Test retrieve pipeline module."""
        url = reverse('pipeline-module-details', kwargs={'pk': self.module.uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pipeline_module_read_by_name(self):
        """Test retrieve pipeline module."""
        url = reverse('pipeline-modules-by-name', kwargs={
            'pk': self.pipeline.uuid,
            'name': self.module.name,
            'version': self.module.version,
        })
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pipeline_create(self):
        """Test create pipeline."""
        self.client.force_authenticate(user=self.user)

        url = reverse('pipeline-create')
        data = {'name': 'Test Pipeline HKLUKD'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pipeline.objects.count(), 2)

    def test_pipeline_module_create(self):
        """Test create pipeline module."""
        self.client.force_authenticate(user=self.user)

        url = reverse('pipeline-module-create')
        data = {
            'pipeline': self.pipeline.uuid,
            'name': 'Test Module YJKAGJD',
            'version': 'vYJKAGJD'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PipelineModule.objects.count(), 2)
        self.assertEqual(self.pipeline.modules.count(), 2)

    def test_pipeline_module_create_with_dependencies(self):
        """Test create pipeline module."""
        self.client.force_authenticate(user=self.user)

        url = reverse('pipeline-module-create')
        data = {
            'pipeline': self.pipeline.uuid,
            'name': 'Test Module YJKAGJD',
            'version': 'vYJKAGJD',
            'dependencies': [self.module.uuid],
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.module.downstreams.count(), 1)


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
