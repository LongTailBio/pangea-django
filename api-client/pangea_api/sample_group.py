
from .remote_object import RemoteObject
from .sample import Sample
from .analysis_result import SampleGroupAnalysisResult


class SampleGroup(RemoteObject):

    def __init__(self, knex, org, name, is_library=False):
        super().__init__(self)
        self.knex = knex
        self.org = org
        self.name = name
        self.is_library = is_library

    def load_blob(self, blob):
        self.uuid = blob['uuid']
        self.created_at = blob['created_at']
        self.updated_at = blob['updated_at']
        self.is_library = blob['is_library']

    def nested_url(self):
        return self.org.nested_url() + f'/sample_groups/{self.name}'

    def _get(self):
        """Fetch the result from the server."""
        self.org.idem()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)

    def _create(self):
        self.org.idem()
        blob = self.knex.post(f'sample_groups?format=json', json={
            'organization': self.org.uuid,
            'name': self.name,
            'is_library': self.is_library,
        })
        self.load_blob(blob)

    def sample(self, sample_name, metadata={}):
        return Sample(self.knex, self, sample_name, metadata=metadata)

    def analysis_result(self, module_name, replicate=None):
        return SampleGroupAnalysisResult(self.knex, self, module_name, replicate=replicate)

