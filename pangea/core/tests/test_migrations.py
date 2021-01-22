
from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestDirectMigration(MigratorTestCase):
    """This class is used to test direct migrations."""

    migrate_from = ('core', '0011_auto_20210122_1522')  # versioned metadata exists but is empty
    migrate_to =   ('core', '0013_auto_20210122_1547')  # metadata moved from sample to vmeta

    def prepare(self):
        """Prepare some data before the migration."""
        org = self.old_state.apps.get_model('core', 'Organization').objects.create(name='an_org JKHGGHJ')
        grp = self.old_state.apps.get_model('core', 'SampleGroup').objects.create(
            organization=org,
            name='library JKHGGHJ',
            is_library=True,
        )
        lib = self.old_state.apps.get_model('core', 'SampleLibrary').objects.create(group=grp)

        SampleModel = self.old_state.apps.get_model('core', 'Sample')
        SampleModel.objects.create(library=lib, name='A JKHGGHJ', metadata={'a': 'b'})
        SampleModel.objects.create(library=lib, name='C JKHGGHJ', metadata={'c': 'd'})

    def test_migration_main0003(self):
        """Run the test itself."""
        VMModel = self.new_state.apps.get_model('core', 'VersionedMetadata')

        self.assertEqual(VMModel.objects.count(), 2)
        virtual_metadatas = {vm.sample.name: vm.metadata for vm in VMModel.objects.all()}
        self.assertEqual(virtual_metadatas['A JKHGGHJ']['a'], 'b')
        self.assertEqual(virtual_metadatas['C JKHGGHJ']['c'], 'd')
