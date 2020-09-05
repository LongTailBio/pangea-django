"""Test suite for Sample model."""
import os
from django.test import TestCase
from django.db.utils import IntegrityError
from unittest import skip

from ..encrypted_fields import EncryptedString
from ..models import (
    PangeaUser,
    Organization,
    S3ApiKey,
    S3Bucket,
    SampleGroup,
    Sample,
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
    Project,
)


class TestUserModel(TestCase):

    def test_personal_org_from_user(self):
        user = PangeaUser.objects.create(email='foo@bar.com')
        org = user.personal_org
        self.assertTrue(org.uuid)
        self.assertTrue(org.created_at)
        self.assertEqual(org.name, user._personal_org_name)
        self.assertEqual(org.uuid, user.personal_org_uuid)
        self.assertIn(user, org.users.all())


class TestS3ApiKeyModel(TestCase):

    def test_encrypt_on_save(self):
        org = Organization.objects.create(name='Test Organization')
        bucket = S3Bucket.objects.create(
            organization=org,
            name='test_bucket',
            endpoint_url='https://sys.foobar.com',                        
        )
        key = S3ApiKey(
            bucket=bucket,
            description='KEY_01',
            public_key='my_public_key',
            private_key='my_private_key',
        )
        key.save()
        self.assertTrue(key.uuid)
        retrieved = S3ApiKey.objects.get(pk=key.uuid)
        self.assertEqual(retrieved.public_key, 'my_public_key')
        self.assertNotEqual(retrieved.private_key, 'my_private_key')
        self.assertTrue(isinstance(retrieved.private_key, EncryptedString))
        self.assertEqual(retrieved.private_key.decrypt(), 'my_private_key')

    def test_get_presigned_url(self):
        pubkey = os.environ.get('PANGEA_S3_TESTER_PUBLIC_KEY', None)
        privkey = os.environ.get('PANGEA_S3_TESTER_PRIVATE_KEY', None)
        if not (pubkey and privkey):
            return  # Only run this test if the keys are available
        org = Organization.objects.create(name='Test Organization')
        bucket = S3Bucket.objects.create(
            organization=org,
            name='pangea.test.bucket',
            endpoint_url='https://s3.wasabisys.com',
        )
        key = S3ApiKey(
            bucket=bucket,
            description='KEY_01',
            public_key=pubkey,
            private_key=privkey,
        )
        key.save()
        retrieved = S3ApiKey.objects.get(pk=key.uuid)
        url = retrieved.presign_url(
            'https://s3.wasabisys.com',
            's3://pangea.test.bucket/my_private_s3_test_file.txt'
        )
        self.assertTrue(
            url.startswith('https://s3.wasabisys.com/pangea.test.bucket/my_private_s3_test_file.txt')
        )
        self.assertIn('AWSAccessKeyId=', url)
        self.assertIn('Signature=', url)
        self.assertIn('Expires=', url)


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


class TestProject(TestCase):
    """Test suite for Project model."""

    def test_add_project(self):
        """Ensure sample model is created correctly."""
        org = Organization.objects.create(name='an_org UYDFG')
        proj = Project.objects.create(
            name='project_01 UYDFG',
            organization=org,
        )
        self.assertTrue(proj.uuid)
        self.assertEqual(proj.name, 'SMPL_01 UYDFG')
        self.assertTrue(proj.created_at)


class TestSampleGroupModel(TestCase):
    """Test suite for SampleGroup model."""

    def test_add_sample_group(self):
        """Ensure sample group model is created correctly."""
        org = Organization.objects.create(name='an_org HJGKTYU')
        group = org.create_sample_group(name='GRP_01 HJGKTYU')
        self.assertTrue(group.uuid)
        self.assertEqual(group.name, 'GRP_01 HJGKTYU')
        self.assertTrue(group.created_at)

    def test_core_sample_group_from_org(self):
        """Ensure we can get a core sample group from an organization."""
        org = Organization.objects.create(name='an_org TYFGHG')
        group = org.core_sample_group
        self.assertTrue(group.uuid)
        self.assertEqual(group.name, org._core_sample_group_name)
        self.assertEqual(group.uuid, org.core_sample_group_uuid)
        self.assertEqual(group.organization, org)
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

    def test_add_ar_with_metadata_to_sample(self):
        """Ensure sample model is created correctly."""
        org = Organization.objects.create(name='an_org EWRVB')
        lib = org.create_sample_group(name='LBRY_01 EWRVB', is_library=True)
        smp = lib.create_sample(name='SMPL_01 EWRVB', metadata={'subject_group': 1})
        ar = smp.create_analysis_result(module_name='module_1', metadata={'foo': 'bar'})
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
