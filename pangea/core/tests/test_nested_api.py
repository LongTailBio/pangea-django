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


class NestedSampleGroupTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization HJDH')
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')

    def test_create_sample_group(self):
        """Ensure authorized user can create sample group."""
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)

        url = reverse('nested-sample-group-create', kwargs={'org_pk': self.organization.pk})
        data = {'name': 'Test Sample Group HJKHJ', 'organization': self.organization.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleGroup.objects.count(), 1)
        self.assertEqual(SampleGroup.objects.get().name, 'Test Sample Group HJKHJ')

    def test_create_sample_group_with_name(self):
        """Ensure authorized user can create sample group."""
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)

        url = reverse('nested-sample-group-create', kwargs={'org_pk': self.organization.name})
        data = {'name': 'Test Sample Group NBYTU', 'organization': self.organization.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleGroup.objects.count(), 1)
        self.assertEqual(SampleGroup.objects.get().name, 'Test Sample Group NBYTU')

    def test_retrieve_sample_group(self):
        """Ensure authorized user can create sample group."""
        grp_name = 'Test Sample Group HGJHJ'
        self.organization.create_sample_group(name=grp_name, is_public=True)

        url = reverse('nested-sample-group-detail', kwargs={
            'org_pk': self.organization.pk,
            'grp_pk': grp_name,
        })
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_sample_group_case_insensitive(self):
        """Ensure authorized user can create sample group."""
        grp_name = 'Test Sample Group TRUGKH'
        self.organization.create_sample_group(name=grp_name, is_public=True)

        url = reverse('nested-sample-group-detail', kwargs={
            'org_pk': self.organization.pk,
            'grp_pk': grp_name.lower(),
        })
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)



class NestedSampleTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization EWKKK')
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')

    def test_create_sample(self):
        """Ensure authorized user can create sample group."""
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)

        sample_library = self.organization.create_sample_group(name='Test Library JKLLL', is_library=True)
        url = reverse('nested-sample-create', kwargs={
            'org_pk': self.organization.pk,
            'grp_pk': sample_library.pk,
        })
        data = {'name': 'Test Sample JKLLL', 'library': sample_library.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sample.objects.count(), 1)
        self.assertEqual(Sample.objects.get().name, 'Test Sample JKLLL')
        self.assertTrue(sample_library.sample_set.filter(pk=response.data.get('uuid')).exists())

    def test_create_sample_with_name(self):
        """Ensure authorized user can create sample group."""
        self.organization.users.add(self.user)
        self.client.force_authenticate(user=self.user)

        sample_library = self.organization.create_sample_group(name='Test Library', is_library=True)
        url = reverse('nested-sample-create', kwargs={
            'org_pk': self.organization.name,
            'grp_pk': sample_library.name,
        })
        data = {'name': 'Test Sample', 'library': sample_library.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sample.objects.count(), 1)
        self.assertEqual(Sample.objects.get().name, 'Test Sample')
        self.assertTrue(sample_library.sample_set.filter(pk=response.data.get('uuid')).exists())

    def test_retrieve_sample(self):
        """Ensure authorized user can create sample group."""
        grp = self.organization.create_sample_group(
            name='Test Sample Group KKJSGHFG',
            is_public=True,
            is_library=True,
        )
        grp.create_sample(name='Test Sample KKJSGHFG')

        url = reverse('nested-sample-details', kwargs={
            'org_pk': self.organization.pk,
            'grp_pk': grp.name,
            'sample_pk': 'Test Sample KKJSGHFG',
        })
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AnalysisResultTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name='Test Organization')
        cls.user = PangeaUser.objects.create(email='user@domain.com', password='Foobar22')
        cls.organization.users.add(cls.user)
        cls.sample_group = cls.organization.create_sample_group(name='Test Library', is_library=True)
        cls.sample_library = cls.sample_group.library
        cls.sample = Sample.objects.create(name='Test Sample', library=cls.sample_library)

    def test_create_sample_group_analysis_result(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('nested-sample-group-ar-create', kwargs={
            'org_pk': self.organization.pk,
            'grp_pk': self.sample_library.pk,
        })
        data = {'module_name': 'taxa', 'sample_group': self.sample_group.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleGroupAnalysisResult.objects.count(), 1)
        self.assertEqual(SampleGroupAnalysisResult.objects.get().sample_group, self.sample_group)
        self.assertEqual(SampleGroupAnalysisResult.objects.get().module_name, 'taxa')

    def test_create_sample_analysis_result(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('nested-sample-ar-create', kwargs={
            'org_pk': self.organization.pk,
            'grp_pk': self.sample_library.pk,
            'sample_pk': self.sample.pk,
        })
        data = {'module_name': 'taxa', 'sample': self.sample.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleAnalysisResult.objects.count(), 1)
        self.assertEqual(SampleAnalysisResult.objects.get().sample, self.sample)
        self.assertEqual(SampleAnalysisResult.objects.get().module_name, 'taxa')

    def test_create_sample_group_analysis_result_with_name(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('nested-sample-group-ar-create', kwargs={
            'org_pk': self.organization.name,
            'grp_pk': self.sample_library.group.name,
        })
        data = {'module_name': 'taxa', 'sample_group': self.sample_group.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleGroupAnalysisResult.objects.count(), 1)
        self.assertEqual(SampleGroupAnalysisResult.objects.get().sample_group, self.sample_group)
        self.assertEqual(SampleGroupAnalysisResult.objects.get().module_name, 'taxa')

    def test_create_sample_analysis_result_with_name(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('nested-sample-ar-create', kwargs={
            'org_pk': self.organization.name,
            'grp_pk': self.sample_library.group.name,
            'sample_pk': self.sample.name,
        })
        data = {'module_name': 'taxa', 'sample': self.sample.pk}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SampleAnalysisResult.objects.count(), 1)
        self.assertEqual(SampleAnalysisResult.objects.get().sample, self.sample)
        self.assertEqual(SampleAnalysisResult.objects.get().module_name, 'taxa')
