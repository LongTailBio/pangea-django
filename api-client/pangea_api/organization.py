
from .remote_object import RemoteObject
from .sample_group import SampleGroup


class Organization(RemoteObject):
    remote_fields = [
        'uuid',
        'created_at',
        'updated_at',
        'name',
    ]
    parent_field = None

    def __init__(self, knex, name):
        super().__init__(self)
        self.knex = knex
        self.name = name

    def nested_url(self):
        return f'nested/{self.name}'

    def _save(self):
        data = {
            field: getattr(self, field)
            for field in self.remote_fields if hasattr(self, field)
        }
        url = f'organizations/{self.uuid}'
        self.knex.put(url, json=data)

    def _get(self):
        """Fetch the result from the server."""
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)

    def _create(self):
        blob = self.knex.post(f'organizations', json={'name': self.name})
        self.load_blob(blob)

    def sample_group(self, group_name, is_library=False):
        return SampleGroup(self.knex, self, group_name, is_library=is_library)
