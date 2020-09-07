
import os
import json
import requests
import time
from os.path import join, basename, getsize

from .remote_object import RemoteObject, RemoteObjectError
from urllib.request import urlretrieve
from tempfile import NamedTemporaryFile

from .constants import FIVE_MB


class AnalysisResult(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'module_name',
        'replicate',
        'metadata',
        'description',
    ]

    def _get(self):
        """Fetch the result from the server."""
        self.parent.idem()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)


class SampleAnalysisResult(AnalysisResult):
    parent_field = 'sample'

    def __init__(self, knex, sample, module_name, replicate=None, metadata={}):
        super().__init__(self)
        self.knex = knex
        self.sample = sample
        self.parent = self.sample
        self.module_name = module_name
        self.replicate = replicate
        self._get_field_cache = []
        self.metadata = metadata

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

    def get_fields(self, cache=True):
        """Return a list of ar-fields fetched from the server."""
        if cache and self._get_field_cache:
            for field in self._get_field_cache:
                yield field
            return
        url = f'sample_ar_fields?analysis_result_id={self.uuid}'
        result = self.knex.get(url)
        for result_blob in result['results']:
            result = self.field(result_blob['name'])
            result.load_blob(result_blob)
            # We just fetched from the server so we change the RemoteObject
            # meta properties to reflect that
            result._already_fetched = True
            result._modified = False
            if cache:
                self._get_field_cache.append(result)
            else:
                yield result
        if cache:
            for field in self._get_field_cache:
                yield field


class SampleGroupAnalysisResult(AnalysisResult):
    parent_field = 'grp'

    def __init__(self, knex, grp, module_name, replicate=None, metadata={}):
        super().__init__(self)
        self.knex = knex
        self.grp = grp
        self.parent = self.grp
        self.module_name = module_name
        self.replicate = replicate
        self.metadata = metadata

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
        self._cached_filename = None  # Used if the field points to S3, FTP, etc
        self._temp_filename = False

    def nested_url(self):
        return self.parent.nested_url() + f'/fields/{self.name}'

    def get_blob_filename(self):
        sname = self.parent.parent.name.replace('.', '-')
        mname = self.parent.module_name.replace('.', '-')
        fname = self.name.replace('.', '-')
        filename = join(
            self.parent.parent.name, f'{sname}.{mname}.{fname}.json'
        ).replace('::', '__')
        return filename

    def get_referenced_filename(self):
        key = None
        for key in ['filename', 'uri', 'url']:
            if key in self.stored_data:
                break
        if key is None:
            raise TypeError('Cannot make a reference filename for a BLOB type result field.')
        ext = self.stored_data[key].split('.')[-1]
        if ext in ['gz']:
            ext = self.stored_data[key].split('.')[-2] + '.' + ext
        sname = self.parent.parent.name.replace('.', '-')
        mname = self.parent.module_name.replace('.', '-')
        fname = self.name.replace('.', '-')
        filename = join(
            self.parent.parent.name, f'{sname}.{mname}.{fname}.{ext}'
        ).replace('::', '__')
        return filename

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
        if json.loads(json.dumps(self.stored_data)) != self.stored_data:
            raise RemoteObjectError('JSON Serialization modifies object')
        self.parent.idem()
        data = {
            'analysis_result': self.parent.uuid,
            'name': self.name,
            'stored_data': self.stored_data,
        }
        blob = self.knex.post(f'{self.canon_url()}?format=json', json=data)
        self.load_blob(blob)

    def download_file(self, filename=None, cache=True):
        """Return a local filepath to the file this result points to."""
        blob_type = self.stored_data.get('__type__', '').lower()
        if blob_type not in ['s3', 'sra']:
            raise TypeError('Cannot fetch a file for a BLOB type result field.')
        if cache and self._cached_filename:
            return self._cached_filename
        if blob_type == 's3':
            return self._download_s3(filename, cache)
        elif blob_type == 'sra':
            return self._download_sra(filename, cache)

    def _download_s3(self, filename, cache):
        try:
            url = self.stored_data['presigned_url']
        except KeyError:
            url = self.stored_data['uri']
        if url.startswith('s3://'):
            url = self.stored_data['endpoint_url'] + '/' + url[5:]
        if not filename:
            self._temp_filename = True
            myfile = NamedTemporaryFile(delete=False)
            myfile.close()
            filename = myfile.name
        urlretrieve(url, filename)
        if cache:
            self._cached_filename = filename
        return filename

    def _download_sra(self, filename, cache):
        url = self.stored_data['url']
        if not filename:
            self._temp_filename = True
            myfile = NamedTemporaryFile(delete=False)
            myfile.close()
            filename = myfile.name
        urlretrieve(url, filename)
        if cache:
            self._cached_filename = filename
        return filename

    def upload_small_file(self, filepath):
        url = f'/{self.canon_url()}/{self.uuid}/upload_s3'
        filename = basename(filepath)
        response = self.knex.post(url, json={'filename': filename})
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f)}
            requests.post(  # Not a call to pangea so we do not use knex
                response['url'],
                data=response['fields'],
                files=files
            )
        return self

    def upload_large_file(self, filepath, file_size, chunk_size=FIVE_MB, max_retries=3, logger=lambda x: x):
        n_parts = int(file_size / chunk_size) + 1
        response = self.knex.post(
            f'/{self.canon_url()}/{self.uuid}/upload_s3',
            json={
                'filename': basename(filepath),
                'n_parts': n_parts,
                'stance': 'upload-multipart',
            }
        )
        parts, urls, upload_id = [], response['urls'], response['upload_id']
        logger(f'[INFO] Starting upload for "{filepath}"')
        with open(filepath, 'rb') as f:
            for num, url in enumerate(urls):
                file_data = f.read(chunk_size)
                attempts = 0
                while attempts < max_retries:
                    try:
                        http_response = requests.put(url, data=file_data)
                        http_response.raise_for_status()
                        break
                    except requests.exceptions.HTTPError:
                        logger(f'[WARN] Upload for part {num + 1} failed. Attempt {attempts + 1}')
                        attempts += 1
                        if attempts == max_retries:
                            raise
                        time.sleep(10 ** attempts)  # exponential backoff, (10 ** 2)s default max
                parts.append({
                    'ETag': http_response.headers['ETag'],
                    'PartNumber': num + 1
                })
                logger(f'[INFO] Uploaded part {num + 1} of {len(urls)} for "{filepath}"')
        response = self.knex.post(
            f'/{self.canon_url()}/{self.uuid}/complete_upload_s3',
            json={
                'parts': parts,
                'upload_id': upload_id,
            },
            json_response=False,
        )
        logger(f'[INFO] Finished Upload for "{filepath}"')
        return self

    def upload_file(self, filepath, multipart_thresh=FIVE_MB, **kwargs):
        file_size = getsize(filepath)
        if file_size >= multipart_thresh:
            return self.upload_large_file(filepath, file_size, **kwargs)
        return self.upload_small_file(filepath)

    def __del__(self):
        if self._temp_filename and self._cached_filename:
            os.remove(self._cached_filename)


class SampleAnalysisResultField(AnalysisResultField):

    def canon_url(self):
        return 'sample_ar_fields'


class SampleGroupAnalysisResultField(AnalysisResultField):

    def canon_url(self):
        return 'sample_group_ar_fields'
