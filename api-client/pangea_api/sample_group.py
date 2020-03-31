
from .remote_object import RemoteObject
from .sample import Sample
from .analysis_result import SampleGroupAnalysisResult


class SampleGroup(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'name',
        'is_library',
        'is_public',
    ]
    parent_field = 'org'

    def __init__(self, knex, org, name, is_library=False):
        super().__init__(self)
        self.knex = knex
        self.org = org
        self.name = name
        self.is_library = is_library

    def nested_url(self):
        return self.org.nested_url() + f'/sample_groups/{self.name}'

    def _save(self):
        data = {
            field: getattr(self, field)
            for field in self.remote_fields if hasattr(self, field)
        }
        data['organization'] = self.org.uuid
        url = f'sample_groups/{self.uuid}'
        self.knex.put(url, json=data)

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

