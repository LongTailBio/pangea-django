
from .remote_object import RemoteObject


class Sample(RemoteObject):

    def __init__(self, knex, grp, name, is_library=False):
        super().__init__(self)
        self.knex = knex
        self.grp = grp
        self.name = name

    def load_blob(self, blob):
        self.uuid = blob['uuid']
        self.created_at = blob['created_at']
        self.updated_at = blob['updated_at']

    def nested_url(self):
        return self.grp.nested_url() + f'/samples/{self.name}'

    def _get(self):
        """Fetch the result from the server."""
        self.org.idem()
        blob = self.knex.get(self.nested_url())
        self.load_blob(blob)

    def _create(self):
        self.org.idem()
        blob = self.knex.post(f'samples?format=json', json={
            'sample_group': self.org.uuid,
            'name': org_name
        })
        self.load_blob(blob)
