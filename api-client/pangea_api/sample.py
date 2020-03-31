
from .remote_object import RemoteObject
from .analysis_result import SampleAnalysisResult


class Sample(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'name',
        'metadata',
        'library'
    ]
    parent_field = 'lib'

    def __init__(self, knex, lib, name, metadata={}):
        super().__init__(self)
        self.knex = knex
        self.lib = lib
        self.name = name
        self.metadata = metadata

    def nested_url(self):
        return self.lib.nested_url() + f'/samples/{self.name}'

    def _save(self):
        data = {
            field: getattr(self, field)
            for field in self.remote_fields if hasattr(self, field)
        }
        data['library'] = self.lib.uuid
        url = f'samples/{self.uuid}'
        self.knex.put(url, json=data)

    def _get(self):
        """Fetch the result from the server."""
        self.lib.get()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)

    def _create(self):
        assert self.lib.is_library
        self.lib.idem()
        data = {
            'library': self.lib.uuid,
            'name': self.name,
        }
        url = 'samples?format=json'
        blob = self.knex.post(url, json=data)
        self.load_blob(blob)

    def analysis_result(self, module_name, replicate=None):
        return SampleAnalysisResult(self.knex, self, module_name, replicate=replicate)
