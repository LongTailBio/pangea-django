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
        url = reverse('treeoflife-correct-taxa-names') + '?query=Bacillus coli'
        response = self.client.get(url, format='json')
        names = {el['name'] for el in response.data['names']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Escherichia coli', names)
        self.assertEqual(1, len(names))

    def test_search_taxa_name(self):
        """Ensure we can update a defunct taxa name."""
        url = reverse('treeoflife-correct-taxa-names') + '?query=Escherichia'
        response = self.client.get(url, format='json')
        names = {el['name'] for el in response.data['names']}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Shigella dysenteriae', names)
        self.assertIn('Escherichia coli', names)
        self.assertTrue(len(names) >= 10)
