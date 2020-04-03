
from .remote_object import RemoteObject


class AnalysisResult(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'module_name',
        'replicate',
    ]

    def _get(self):
        """Fetch the result from the server."""
        self.parent.idem()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)


class SampleAnalysisResult(AnalysisResult):
    parent_field = 'sample'

    def __init__(self, knex, sample, module_name, replicate=None):
        super().__init__(self)
        self.knex = knex
        self.sample = sample
        self.parent = self.sample
        self.module_name = module_name
        self.replicate = replicate

    def nested_url(self):
        return self.sample.nested_url() + f'/analysis_results/{self.module_name}'

    def _save(self):
        data = {
            field: getattr(self, field)
            for field in self.remote_fields if hasattr(self, field)
        }
        data['sample'] = self.sample.uuid
        url = f'sample_ars/{self.uuid}'
        self.knex.put(url, json=data)

    def _create(self):
        self.sample.idem()
        data = {
            'sample': self.sample.uuid,
            'module_name': self.module_name,
        }
        if self.replicate:
            data['replicate'] = self.replicate
        blob = self.knex.post(f'sample_ars?format=json', json=data)
        self.load_blob(blob)

    def field(self, field_name, data={}):
        return SampleAnalysisResultField(self.knex, self, field_name, data=data)

    def get_fields(self):
        """Return a list of ar-fields fetched from the server."""
        url = f'sample_ar_fields?analysis_result_id={self.uuid}'
        result = self.knex.get(url)
        for result_blob in result['results']:
            result = self.field(result_blob['name'])
            result.load_blob(result_blob)
            # We just fetched from the server so we change the RemoteObject
            # meta properties to reflect that
            result._already_fetched = True
            result._modified = False
            yield result


class SampleGroupAnalysisResult(AnalysisResult):
    parent_field = 'grp'

    def __init__(self, knex, grp, module_name, replicate=None):
        super().__init__(self)
        self.knex = knex
        self.grp = grp
        self.parent = self.grp
        self.module_name = module_name
        self.replicate = replicate

    def nested_url(self):
        return self.grp.nested_url() + f'/analysis_results/{self.module_name}'

    def _save(self):
        data = {
            field: getattr(self, field)
            for field in self.remote_fields if hasattr(self, field)
        }
        data['sample_group'] = self.grp.uuid
        url = f'sample_group_ars/{self.uuid}'
        self.knex.put(url, json=data)

    def _create(self):
        self.grp.idem()
        data = {
            'sample_group': self.grp.uuid,
            'module_name': self.module_name,
        }
        if self.replicate:
            data['replicate'] = self.replicate
        blob = self.knex.post(f'sample_group_ars?format=json', json=data)
        self.load_blob(blob)

    def field(self, field_name, data={}):
        return SampleGroupAnalysisResultField(self.knex, self, field_name, data=data)

    def get_fields(self):
        """Return a list of ar-fields fetched from the server."""
        url = f'sample_group_ar_fields?analysis_result_id={self.uuid}'
        result = self.knex.get(url)
        for result_blob in result['results']:
            result = self.field(result_blob['name'])
            result.load_blob(result_blob)
            # We just fetched from the server so we change the RemoteObject
            # meta properties to reflect that
            result._already_fetched = True
            result._modified = False
            yield result


class AnalysisResultField(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'name',
        'stored_data',
    ]
    parent_field = 'parent'

    def __init__(self, knex, parent, field_name, data={}):
        super().__init__(self)
        self.knex = knex
        self.parent = parent
        self.name = field_name
        self.stored_data = data

    def nested_url(self):
        return self.parent.nested_url() + f'/fields/{self.name}'

    def _save(self):
        data = {
            field: getattr(self, field)
            for field in self.remote_fields if hasattr(self, field)
        }
        data['analysis_result'] = self.parent.uuid
        url = f'{self.canon_url()}/{self.uuid}'
        self.knex.put(url, json=data)

    def _get(self):
        """Fetch the result from the server."""
        self.parent.idem()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)

    def _create(self):
        self.parent.idem()
        data = {
            'analysis_result': self.parent.uuid,
            'name': self.name,
            'stored_data': self.stored_data,
        }
        blob = self.knex.post(f'{self.canon_url()}?format=json', json=data)
        self.load_blob(blob)


class SampleAnalysisResultField(AnalysisResultField):

    def canon_url(self):
        return 'sample_ar_fields'


class SampleGroupAnalysisResultField(AnalysisResultField):

    def canon_url(self):
        return 'sample_group_ar_fields'
