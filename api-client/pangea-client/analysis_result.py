
from .remote_object import RemoteObject


class AnalysisResult(RemoteObject):

    def load_blob(self, blob):
        self.uuid = blob['uuid']
        self.created_at = blob['created_at']
        self.updated_at = blob['updated_at']

    def _get(self):
        """Fetch the result from the server."""
        self.org.idem()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)


class SampleAnalysisResult(AnalysisResult):

    def __init__(self, knex, module_name, replicate=None):
        super().__init__(self)
        self.knex = knex
        self.sample = sample
        self.name = name

    def nested_url(self):
        return self.sample.nested_url() + f'/analysis_results/{self.name}'

    def _create(self):
        self.org.idem()
        blob = self.knex.post(f'sample_ars?format=json', json={
            'sample': self.sample.uuid,
            'module_name': self.module_name,
        })
        self.load_blob(blob)

    def field(self, field_name, data=None):
        return SampleAnalysisResultField(field_name)


class SampleGroupAnalysisResult(AnalysisResult):

    def __init__(self, knex, module_name, replicate=None):
        super().__init__(self)
        self.knex = knex
        self.grp = grp
        self.module_name = module_name

    def nested_url(self):
        return self.grp.nested_url() + f'/analysis_results/{self.name}'

    def _create(self):
        self.org.idem()
        blob = self.knex.post(f'sample_group_ars?format=json', json={
            'sample_group': self.grp.uuid,
            'module_name': self.module_name,
        })
        self.load_blob(blob)

    def field(self, field_name, data=None):
        return SampleGroupAnalysisResultField()


class AnalysisResultField(RemoteObject):

    def __init__(self, knex, parent, field_name, data=None):
        self.knex = knex
        self.parent = parent
        self.field_name = field_name
        self.data = data

    def nested_url(self):
        return self.parent.nested_url() + f'/field/{self.field_name}/'

    def _get(self):
        """Fetch the result from the server."""
        self.org.idem()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)

    def load_blob(self, blob):
        self.uuid = blob['uuid']
        self.created_at = blob['created_at']
        self.updated_at = blob['updated_at']

    def _create(self):
        self.parent.idem()
        blob = self.knex.post(f'{self.canon_url}?format=json', json={
            'analysis_result': self.parent.uuid,
            'name': org_name,
            'stored_data': self.data,
        })
        self.load_blob(blob)


class SampleAnalysisResultField(AnalysisResult):

    def canon_url(self):
        return 'sample_ar_fields'


class SampleGroupAnalysisResultField(AnalysisResult):

    def canon_url(self):
        return 'sample_group_ar_fields'
