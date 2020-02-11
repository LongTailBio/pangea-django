from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.models import (
    Organization,
    Sample,
    SampleAnalysisResult,
    SampleAnalysisResultField,
)


class TaxaSearchTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        organization = Organization.objects.create(name='Test Organization')
        sample_group = organization.create_sample_group(name='Test Library', is_library=True)
        sample_library = sample_group.library
        sample_01 = Sample.objects.create(name='Test Sample 01',
                                          metadata={'foo': 'bar'},
                                          library=sample_library)
        sample_02 = Sample.objects.create(name='Test Sample 02', library=sample_library)
        analysis_result_01 = SampleAnalysisResult.objects.create(module_name='taxa', sample=sample_01)
        analysis_result_02 = SampleAnalysisResult.objects.create(module_name='taxa', sample=sample_02)
        stored_data_01 = {"e. coli": 0.32, "enterococcus": 0.79}
        stored_data_02 = {"e. coli": 0.56}
        taxa_field_01 = SampleAnalysisResultField.objects.create(name='relative_abundance',
                                                                 analysis_result=analysis_result_01,
                                                                 stored_data=stored_data_01)
        taxa_field_02 = SampleAnalysisResultField.objects.create(name='relative_abundance',
                                                                 analysis_result=analysis_result_02,
                                                                 stored_data=stored_data_02)

    def test_detailed_match(self):
        """Check that a detailed query returns appropriatelylimited results."""
        url = reverse('taxa-search')
        data = {'query': 'enterococcus'}
        response = self.client.get(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(len(response.data['results']['enterococcus']), 1)
        matching_sample = response.data['results']['enterococcus'][0]
        self.assertEqual(matching_sample['sample_name'], 'Test Sample 01')
        with self.assertRaises(KeyError):
            matching_sample['metadata']

    def test_fuzzy_match(self):
        """Check that a detailed query returns appropriatelylimited results."""
        url = reverse('taxa-search')
        data = {'query': 'e'}
        response = self.client.get(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(len(response.data['results']['enterococcus']), 1)
        entero_sample = response.data['results']['enterococcus'][0]
        self.assertEqual(entero_sample['sample_name'], 'Test Sample 01')
        ecoli_samples = response.data['results']['e. coli']
        self.assertEqual(len(ecoli_samples), 2)
        ecoli_names = [sample['sample_name'] for sample in ecoli_samples]
        self.assertIn('Test Sample 01', ecoli_names)
        self.assertIn('Test Sample 02', ecoli_names)

    def test_include_metadata(self):
        """Check that a detailed query returns appropriatelylimited results."""
        url = reverse('taxa-search')
        data = {'query': 'enterococcus', 'metadata': 'true'}
        response = self.client.get(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data['results']['enterococcus'][0]['sample_metadata'], {'foo': 'bar'})
