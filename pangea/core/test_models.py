"""Test suite for Sample model."""

from django.test import TestCase
from django.db.utils import IntegrityError

from .models import (
    Organization,
    SampleGroup,
    Sample,
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
)


class TestSampleModel(TestCase):
    """Test suite for Sample model."""

    def test_add_sample(self):
        """Ensure sample model is created correctly."""
        org = Organization.objects.create(name='an_org AFFFS')
        library = SampleGroup.objects.create(
            organization=org,
            name='library AFFFS',
            is_library=True,
        )
        sample = Sample.objects.create(
            name='SMPL_01 AFFFS',
            library=library,
            metadata={'foo': 'bar'}
        )

        self.assertTrue(sample.uuid)
        self.assertEqual(sample.name, 'SMPL_01 AFFFS')
        self.assertEqual(sample.metadata['foo'], 'bar')
        self.assertTrue(sample.created_at)

    def test_add_duplicate_name(self):
        """Ensure duplicate sample names are not allowed."""
        org = Organization.objects.create(name='an_org OIUO')
        lib = org.create_sample_group(name='LBRY_01 OIUO', is_library=True)
        lib.create_sample(name='SMPL_01 OIUO')
        dupe = lambda: lib.create_sample(name='SMPL_01 OIUO')
        self.assertRaises(IntegrityError, dupe)

    def test_different_libraries(self):
        """Ensure duplicate sample names in different libraries are allowed."""
        org = Organization.objects.create(name='an_org UIY')
        lib1 = org.create_sample_group(name='LBRY_01 UIY', is_library=True)
        lib2 = org.create_sample_group(name='LBRY_02 UIY', is_library=True)
        original = lib1.create_sample(name='SMPL_01 UIY')
        duplicate = lib2.create_sample(name='SMPL_01 UIY')
        self.assertEqual(original.name, duplicate.name)
        self.assertNotEqual(original.library.uuid, duplicate.library.uuid)
