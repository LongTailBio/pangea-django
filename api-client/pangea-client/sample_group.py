
from .remote_object import RemoteObject


class SampleGroup(RemoteObject):

    def __init__(self, knex, org, name, is_library=False):
        super().__init__(self)
        self.knex = knex
        self.org = org
        self.name = name

    def load_blob(self, blob):
        self.uuid = blob['uuid']
        self.created_at = blob['created_at']
        self.updated_at = blob['updated_at']

    def _get(self):
        """Fetch the result from the server."""
        self.org.idem()
        blob = self.knex.get(f'nested/{self.org.name}/sample_groups/{self.name}')
        self.load_blob(blob)

    def _create(self):
        self.org.idem()
        blob = self.knex.post(f'sample_groups?format=json', json={
            'organization': self.org.uuid,
            'name': org_name
        })
        self.load_blob(blob)
