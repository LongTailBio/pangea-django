from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.models import (
    PangeaUser,
    Organization,
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
        data = {'user_uuid': self.target_user.pk}
        response = self.client.post(url, data, format='json')
        return response

    def test_unauthenticated_add_user_to_organization(self):
        response = self.add_target_user()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        organizations_queryset = Organization.objects.filter(users__pk=self.target_user.pk)
        self.assertEqual(organizations_queryset.count(), 0)

    def test_unauthorized_add_sample_to_group(self):
        self.client.force_authenticate(user=self.anon_user)
        response = self.add_target_user()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        organizations_queryset = Organization.objects.filter(users__pk=self.target_user.pk)
        self.assertEqual(organizations_queryset.count(), 0)

    def test_authorized_add_sample_to_group(self):
        self.client.force_authenticate(user=self.org_user)
        response = self.add_target_user()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        organizations_queryset = Organization.objects.filter(users__pk=self.target_user.pk)
        self.assertEqual(organizations_queryset.count(), 1)


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


class SampleTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')

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


class AnalysisResultTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.user = PangeaUser.objects.create(email='user@domain.com',password='Foobar22')
        cls.organization.users.add(cls.user)
        cls.sample_group = cls.organization.create_sample_group(name='Test Library', is_library=True)
        cls.sample_library = cls.sample_group.library
        cls.sample = Sample.objects.create(name='Test Sample', library=cls.sample_library)

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
