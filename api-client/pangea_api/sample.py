
from .remote_object import RemoteObject
from .analysis_result import SampleAnalysisResult


class Sample(RemoteObject):

    def __init__(self, knex, grp, name, metadata={}):
        super().__init__(self)
        self.knex = knex
        self.grp = grp
        self.name = name
        self.metadata = metadata

    def load_blob(self, blob):
        self.uuid = blob['uuid']
        self.created_at = blob['created_at']
        self.updated_at = blob['updated_at']

    def nested_url(self):
        return self.grp.nested_url() + f'/samples/{self.name}'

    def _get(self):
        """Fetch the result from the server."""
        self.grp.get()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)

    def _create(self):
        assert self.grp.is_library
        self.grp.idem()
        data = {
            'library': self.grp.uuid,
            'name': self.name,
        }
        url = 'samples?format=json'
        blob = self.knex.post(url, json=data)
        self.load_blob(blob)

    def analysis_result(self, module_name, replicate=None):
        return SampleAnalysisResult(self.knex, self, module_name, replicate=replicate)
