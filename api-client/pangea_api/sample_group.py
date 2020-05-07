
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
        self._sample_cache = []
        self._get_sample_cache = []
        self._get_result_cache = []

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

        for sample in self._sample_cache:
            sample.idem()
            url = f'sample_groups/{self.uuid}/samples'
            self.knex.post(url, json={'sample_uuid': sample.uuid})
        self._sample_cache = []

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

    def add_sample(self, sample):
        """Return this group and add a sample to this group.

        Do not contact server until `.save()` is called on this group.
        """
        self._sample_cache.append(sample)
        self._modified = True
        return self

    def sample(self, sample_name, metadata={}):
        return Sample(self.knex, self, sample_name, metadata=metadata)

    def analysis_result(self, module_name, replicate=None):
        return SampleGroupAnalysisResult(self.knex, self, module_name, replicate=replicate)

    def get_samples(self, cache=True):
        """Yield samples fetched from the server."""
        if cache and self._get_sample_cache:
            for sample in self._get_sample_cache:
                yield sample
            return
        url = f'sample_groups/{self.uuid}/samples'
        result = self.knex.get(url)
        for sample_blob in result['results']:
            sample = self.sample(sample_blob['name'])
            sample.load_blob(sample_blob)
            # We just fetched from the server so we change the RemoteObject
            # meta properties to reflect that
            sample._already_fetched = True
            sample._modified = False
            if cache:
                self._get_sample_cache.append(sample)
            else:
                yield sample
        if cache:
            for sample in self._get_sample_cache:
                yield sample

    def get_analysis_results(self, cache=True):
        """Yield group analysis results fetched from the server."""
        if cache and self._get_result_cache:
            for ar in self._get_result_cache:
                yield ar
            return
        url = f'sample_group_ars?sample_group_id={self.uuid}'
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
        """Return a manifest for this group."""
        url = f'sample_groups/{self.uuid}/manifest'
        return self.knex.get(url)

    def __str__(self):
        return f'<Pangea::SampleGroup {self.name} {self.uuid} />'

    def __repr__(self):
        return f'<Pangea::SampleGroup {self.name} {self.uuid} />'
