"""Test suite for TreeOfLife module."""
from django.urls import reverse
from django.test import TestCase
from django.db.utils import IntegrityError
from unittest import skip
from rest_framework import status
from rest_framework.test import APITestCase

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from pangea.contrib.treeoflife.models import (
    TaxonName,
    TreeNode,
)

from .populate_test_db import populate_test_db


class TestTreeOfLife(TestCase):

    @classmethod
    def setUpTestData(cls):
        populate_test_db()

    def test_get_root_node(self):
        root = TreeNode.objects.get(taxon_id='1')
        self.assertTrue(root.uuid)
        self.assertFalse(root.parent)

    def test_get_root_by_name(self):
        root = TaxonName.objects.get(name__iexact='root')
        self.assertTrue(root.uuid)

    def test_get_specific_genus_by_name(self):
        taxa = TaxonName.objects.get(name__iexact='Escherichia')
        self.assertTrue(taxa.uuid)

    def test_get_specific_species_by_name(self):
        taxa = TaxonName.objects.get(name__iexact='Escherichia coli')
        self.assertTrue(taxa.uuid)


class TestTreeOfLifeAPI(APITestCase):

    @classmethod
    def setUpTestData(cls):
        populate_test_db()

    def test_canonicalize_taxa_name(self):
        """Ensure we can update a defunct taxa name."""
        query = 'Bacillus coli'
        url = reverse('treeoflife-correct-taxa-names') + f'?query={query}'
        response = self.client.get(url, format='json')
        names = {el['name'] for el in response.data[query]['names']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Escherichia coli', names)
        self.assertEqual(1, len(names))

    def test_canonicalize_taxa_name_case_insensitive(self):
        """Ensure we can update a defunct taxa name."""
        query = 'Bacillus coli'.lower()
        url = reverse('treeoflife-correct-taxa-names') + f'?query={query}'
        response = self.client.get(url, format='json')
        names = {el['name'] for el in response.data[query]['names']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Escherichia coli', names)
        self.assertEqual(1, len(names))

    def test_canonicalize_multiple_taxa_name(self):
        """Ensure we can update a defunct taxa name."""
        q1, q2 = 'Bacillus coli', 'Chondromyces aurantiacus'
        url = reverse('treeoflife-correct-taxa-names') + f'?query={q1},{q2}'
        response = self.client.get(url, format='json')
        names1 = {el['name'] for el in response.data[q1]['names']}
        names2 = {el['name'] for el in response.data[q2]['names']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Escherichia coli', names1)
        self.assertEqual(1, len(names1))
        self.assertIn('Stigmatella aurantiaca', names2)
        self.assertEqual(1, len(names2))

    def test_search_taxa_name(self):
        """Ensure we can update a defunct taxa name."""
        query = 'Escherichia'
        url = reverse('treeoflife-correct-taxa-names') + f'?query={query}'
        response = self.client.get(url, format='json')
        names = {el['name'] for el in response.data[query]['names']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Shigella dysenteriae', names)
        self.assertIn('Escherichia coli', names)
        self.assertTrue(len(names) >= 10)

    def test_search_non_canon_name(self):
        """Ensure we can update a defunct taxa name."""
        query = 'Escherichia'
        url = reverse('treeoflife-correct-taxa-names') + f'?query={query}&canon=false'
        response = self.client.get(url, format='json')
        names = {el['name'] for el in response.data[query]['names']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['canon'])
        self.assertIn('Shigella dysenteriae', names)
        self.assertIn('Escherichia coli', names)
        self.assertIn('Bacillus coli', names)
        self.assertTrue(len(names) >= 11)

    def test_search_taxa_name_rank_specified(self):
        """Ensure we can update a defunct taxa name."""
        query = 'Escherichia'
        url = reverse('treeoflife-correct-taxa-names') + f'?query={query}&rank=species'
        response = self.client.get(url, format='json')
        names = {el['name'] for el in response.data[query]['names']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rank'], 'species')
        self.assertIn('Shigella dysenteriae', names)
        self.assertIn('Escherichia coli', names)
        self.assertNotIn('Escherichia', names)
        self.assertTrue(len(names) >= 9)

    def test_get_descendants(self):
        """Ensure we can get descendants."""
        query = 'Escherichia'
        url = reverse('treeoflife-get-descendants') + f'?query={query}'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['depth'], 1)
        self.assertTrue(len(response.data[query]['children']) >= 2)
