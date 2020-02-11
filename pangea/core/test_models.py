"""Test suite for Sample model."""

from django.test import TestCase
from django.db.utils import IntegrityError
from unittest import skip

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
        grp = SampleGroup.factory(
            organization=org,
            name='library AFFFS',
            is_library=True,
        )
        sample = Sample.objects.create(
            name='SMPL_01 AFFFS',
            library=grp.library,
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
        self.assertNotEqual(original.library, duplicate.library)


class TestSampleGroupModel(TestCase):
    """Test suite for SampleGroup model."""

    def test_add_sample_group(self):
        """Ensure sample group model is created correctly."""
        org = Organization.objects.create(name='an_org HJGKTYU')
        group = org.create_sample_group(name='GRP_01 HJGKTYU')
        self.assertTrue(group.uuid)
        self.assertEqual(group.name, 'GRP_01 HJGKTYU')
        self.assertTrue(group.created_at)

    def test_add_duplicate_name(self):
        """Ensure duplicate group names are not allowed."""
        org = Organization.objects.create(name='an_org UBUYJIU')
        org.create_sample_group(name='GRP_01 UBUYJIU')
        dupe = lambda: org.create_sample_group(name='GRP_01 UBUYJIU')
        self.assertRaises(IntegrityError, dupe)

    def test_add_samples(self):
        """Ensure that samples can be added to SampleGroup."""
        org = Organization.objects.create(name='an_org OIUO')
        lib = org.create_sample_group(name='LBRY_01 OIUO', is_library=True)
        sample_one = lib.create_sample(name='SMPL_01 OIUO', metadata={'subject_group': 1})
        sample_two = lib.create_sample(name='SMPL_02 OIUO', metadata={'subject_group': 4})
        grp = org.create_sample_group(name='GRP_01 OIUO', is_library=False)
        grp.add_sample(sample_one)
        grp.add_sample(sample_two)

        samples = grp.sample_set.all()
        sample_uuids = [sample.uuid for sample in samples]
        self.assertEqual(len(samples), 2)
        self.assertIn(sample_one.uuid, sample_uuids)
        self.assertIn(sample_two.uuid, sample_uuids)
        self.assertEqual(len(samples), 2)
        self.assertIn(sample_one, samples)
        self.assertIn(sample_two, samples)


class TestAnalysisResultModel(TestCase):
    """Test suite for Sample model."""

    def test_add_ar_to_sample(self):
        """Ensure sample model is created correctly."""
        org = Organization.objects.create(name='an_org EWRVB')
        lib = org.create_sample_group(name='LBRY_01 EWRVB', is_library=True)
        smp = lib.create_sample(name='SMPL_01 EWRVB', metadata={'subject_group': 1})
        ar = smp.create_analysis_result(module_name='module_1')
        self.assertTrue(ar.uuid)
        self.assertEqual(ar.module_name, 'module_1')
        self.assertEqual(ar.sample, smp)
        self.assertTrue(ar.created_at)

    @skip('TODO')
    def test_add_dependencies_to_ar(self):
        """Ensure sample model is created correctly."""
        org = Organization.objects.create(name='an_org EWRVB')
        lib = org.create_sample_group(name='LBRY_01 EWRVB', is_library=True)
        smp = lib.create_sample(name='SMPL_01 EWRVB', metadata={'subject_group': 1})
        ar = smp.create_analysis_result(module_name='module_1')
        ar.add_dependency_uuids('one-uuid', 'another-uuid')
        self.assertIn('one-uuid', ar.dependency_uuids)
        self.assertIn('another-uuid', ar.dependency_uuids)

    @skip('TODO')
    def test_add_dup_dependencies_to_ar(self):
        """Ensure sample model is created correctly."""
        org = Organization.objects.create(name='an_org EWRVB')
        lib = org.create_sample_group(name='LBRY_01 EWRVB', is_library=True)
        smp = lib.create_sample(name='SMPL_01 EWRVB', metadata={'subject_group': 1})
        ar = smp.create_analysis_result(module_name='module_1')
        ar.add_dependency_uuids('one-uuid', 'another-uuid')
        self.assertIn('one-uuid', ar.dependency_uuids)
        self.assertIn('another-uuid', ar.dependency_uuids)
        ar.add_dependency_uuids('one-uuid', 'third-uuid')
        self.assertIn('third-uuid', ar.dependency_uuids)
        self.assertEqual(3, len(ar.dependency_uuids))

    def test_add_duplicate_module_replicate_to_sample(self):
        """Ensure duplicate sample names with same replicate are not allowed."""
        org = Organization.objects.create(name='an_org EWRVB')
        lib = org.create_sample_group(name='LBRY_01 EWRVB', is_library=True)
        smp = lib.create_sample(name='SMPL_01 EWRVB', metadata={'subject_group': 1})
        smp.create_analysis_result(module_name='module_1', replicate='foo')
        dupe = lambda: smp.create_analysis_result(module_name='module_1', replicate='foo')
        self.assertRaises(IntegrityError, dupe)

    def test_add_duplicate_module_to_sample(self):
        """Ensure duplicate sample names are not allowed."""
        org = Organization.objects.create(name='an_org UIIU')
        lib = org.create_sample_group(name='LBRY_01 UIIU', is_library=True)
        smp = lib.create_sample(name='SMPL_01 UIIU', metadata={'subject_group': 1})
        smp.create_analysis_result(module_name='module_1')
        smp.create_analysis_result(module_name='module_1')
        self.assertEqual(len(smp.analysis_result_set.all()), 2)

    def test_add_duplicate_to_diff_samples(self):
        """Ensure duplicate sample names in different libraries are allowed."""
        org = Organization.objects.create(name='an_org UYH')
        lib = org.create_sample_group(name='LBRY_01 UYH', is_library=True)
        smp1 = lib.create_sample(name='SMPL_01 UYH', metadata={'subject_group': 1})
        orig = smp1.create_analysis_result(module_name='module_1', replicate='foo')
        smp2 = lib.create_sample(name='SMPL_02 UYH', metadata={'subject_group': 1})
        dupe = smp2.create_analysis_result(module_name='module_1', replicate='foo')
        self.assertEqual(orig.module_name, dupe.module_name)
        self.assertEqual(orig.replicate, dupe.replicate)
        self.assertNotEqual(orig.sample, dupe.sample)

    def test_add_ar_to_group(self):
        """Ensure sample model is created correctly."""
        org = Organization.objects.create(name='an_org YNFD')
        lib = org.create_sample_group(name='LBRY_01 YNFD', is_library=True)
        ar = lib.create_analysis_result(module_name='module_1', replicate='foo')
        self.assertTrue(ar.uuid)
        self.assertEqual(ar.module_name, 'module_1')
        self.assertEqual(ar.sample_group, lib)
        self.assertTrue(ar.created_at)

    def test_add_duplicate_module_replicate_to_group(self):
        """Ensure duplicate sample names and with same replicate are not allowed."""
        org = Organization.objects.create(name='an_org MLAS')
        lib = org.create_sample_group(name='LBRY_01 MLAS', is_library=True)
        lib.create_analysis_result(module_name='module_1', replicate='foo')
        dupe = lambda: lib.create_analysis_result(module_name='module_1', replicate='foo')
        self.assertRaises(IntegrityError, dupe)

    def test_add_duplicate_module_to_group(self):
        """Ensure duplicate sample names and with diff replicate are allowed."""
        org = Organization.objects.create(name='an_org YSDAFG')
        lib = org.create_sample_group(name='LBRY_01 YSDAFG', is_library=True)
        lib.create_analysis_result(module_name='module_1')
        lib.create_analysis_result(module_name='module_1')
        self.assertEqual(len(lib.analysis_result_set.all()), 2)

    def test_add_duplicate_to_diff_groups(self):
        """Ensure duplicate sample names in different libraries are allowed."""
        org = Organization.objects.create(name='an_org VFASD')
        lib1 = org.create_sample_group(name='LBRY_01 VFASD', is_library=True)
        lib2 = org.create_sample_group(name='LBRY_02 VFASD', is_library=True)
        orig = lib1.create_analysis_result(module_name='module_1', replicate='foo')
        dupe = lib2.create_analysis_result(module_name='module_1', replicate='foo')
        self.assertEqual(orig.module_name, dupe.module_name)
        self.assertNotEqual(orig.sample_group, dupe.sample_group)