
from .remote_object import RemoteObject
from .analysis_result import SampleAnalysisResult


class Sample(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'name',
        'metadata',
        'library',
    ]
    parent_field = 'lib'

    def __init__(self, knex, lib, name, metadata={}):
        super().__init__(self)
        self.knex = knex
        self.lib = lib
        self.name = name
        self.metadata = metadata
        self._get_result_cache = []

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

    def get_analysis_results(self, cache=True):
        """Yield sample analysis results fetched from the server."""
        if cache and self._get_result_cache:
            for ar in self._get_result_cache:
                yield ar
            return
        url = f'sample_ars?sample_id={self.uuid}'
        result = self.knex.get(url)
        for result_blob in result['results']:
            result = self.analysis_result(result_blob['module_name'])
            result.load_blob(result_blob)
            # We just fetched from the server so we change the RemoteObject
            # meta properties to reflect that
            result._already_fetched = True
            result._modified = False
            if cache:
                self._get_result_cache.append(result)
            else:
                yield result
        if cache:
            for ar in self._get_result_cache:
                yield ar

    def get_manifest(self):
        """Return a manifest for this sample."""
        url = f'samples/{self.uuid}/manifest'
        return self.knex.get(url)

    def __str__(self):
        return f'<Pangea::Sample {self.name} {self.uuid} />'

    def __repr__(self):
        return f'<Pangea::Sample {self.name} {self.uuid} />'
