from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from pangea.core.models import (
    Organization,
    Sample,
    SampleAnalysisResult,
    SampleAnalysisResultField,
)

from .constants import (
    METASUB_GRP_NAME,
    METASUB_ORG_NAME,
    METASUB_LIBRARY_UUID,
)


class MetaSUBTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        organization = Organization.objects.create(name=METASUB_ORG_NAME)
        sample_group = organization.create_sample_group(name=METASUB_GRP_NAME, is_library=True)
        sample_library = sample_group.library
        sample_01 = sample_library.create_sample(name='Test Sample 01',
                                          metadata={
                                            'city': 'new_york_city',
                                            'city_latitude': -30.1,
                                            'city_longitude': 50.2,
                                          })
        sample_02 = sample_library.create_sample(name='Test Sample 02',
                                          metadata={
                                            'city': 'hong_kong',
                                            'city_latitude': 20.0,
                                            'city_longitude': -10.9,
                                          })
        analysis_result_01 = SampleAnalysisResult.objects.create(module_name='pangea::metasub::krakenhll_taxa_abundances', sample=sample_01)
        analysis_result_02 = SampleAnalysisResult.objects.create(module_name='pangea::metasub::krakenhll_taxa_abundances', sample=sample_02)
        stored_data_01 = {"e. coli": 0.32, "enterococcus": 0.79}
        stored_data_02 = {"e. coli": 0.56}
        taxa_field_01 = SampleAnalysisResultField.objects.create(name='relative_abundance',
                                                                 analysis_result=analysis_result_01,
                                                                 stored_data=stored_data_01)
        taxa_field_02 = SampleAnalysisResultField.objects.create(name='relative_abundance',
                                                                 analysis_result=analysis_result_02,
                                                                 stored_data=stored_data_02)

    def test_detailed_match_samples(self):
        """Check that a detailed query returns appropriatelylimited results."""
        url = reverse('metasub-sample-taxa-search')
        data = {'query': 'enterococcus'}
        response = self.client.get(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(len(response.data['results']['enterococcus']), 1)
        matching_sample = response.data['results']['enterococcus'][0]
        self.assertEqual(matching_sample['sample_name'], 'Test Sample 01')
        with self.assertRaises(KeyError):
            matching_sample['metadata']

    def test_fuzzy_match_samples(self):
        """Check that a detailed query returns appropriatelylimited results."""
        url = reverse('metasub-sample-taxa-search')
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

    def test_fuzzy_match_samples_with_metadata(self):
        """Check that a detailed query returns appropriatelylimited results."""
        url = reverse('metasub-sample-taxa-search')
        data = {'query': 'e', 'metadata': 'true'}
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
        self.assertIn('sample_metadata', ecoli_samples[0])

    def test_detailed_match_cities(self):
        """Check that a detailed query returns appropriatelylimited results."""
        url = reverse('metasub-city-taxa-search')
        data = {'query': 'enterococcus'}
        response = self.client.get(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(len(response.data['results']['enterococcus']), 1)
        matching_city = list(response.data['results']['enterococcus'].values())[0]
        self.assertEqual(matching_city['city_name'], 'new_york_city')
