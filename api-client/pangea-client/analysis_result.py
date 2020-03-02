
from .remote_object import RemoteObject


class AnalysisResult(RemoteObject):

    def load_blob(self, blob):
        self.uuid = blob['uuid']
        self.created_at = blob['created_at']
        self.updated_at = blob['updated_at']


class SampleAnalysisResult(AnalysisResult):

    def __init__(self, knex, sample, name, is_library=False):
        super().__init__(self)
        self.knex = knex
        self.sample = sample
        self.name = name

    def nested_url(self):
        return self.sample.nested_url() + f'/analysis_results/{self.name}'

    def _get(self):
        """Fetch the result from the server."""
        self.org.idem()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)

    def _create(self):
        self.org.idem()
        blob = self.knex.post(f'sample_ars?format=json', json={
            'sample_group': self.org.uuid,
            'name': org_name
        })
        self.load_blob(blob)


class SampleGroupAnalysisResult(AnalysisResult):

    def __init__(self, knex, grp, name, is_library=False):
        super().__init__(self)
        self.knex = knex
        self.grp = grp
        self.name = name

    def nested_url(self):
        return self.grp.nested_url() + f'/analysis_results/{self.name}'

    def _get(self):
        """Fetch the result from the server."""
        self.org.idem()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)

    def _create(self):
        self.org.idem()
        blob = self.knex.post(f'sample_group_ars?format=json', json={
            'sample_group': self.org.uuid,
            'name': org_name
        })
        self.load_blob(blob)
