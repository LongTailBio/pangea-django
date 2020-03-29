
from requests.exceptions import HTTPError


class RemoteObject:

    def __init__(self, *args, **kwargs):
        self.already_fetched = False
        self.deleted = False

    def get(self):
        if not self.already_fetched:
            self._get()
        self.already_fetched = True
        return self

    def create(self):
        if not self.already_fetched:
            self._create()
        self.already_fetched = True
        return self

    def load_blob(self, blob):
        self.uuid = blob['uuid']
        self.created_at = blob['created_at']
        self.updated_at = blob['updated_at']

    def idem(self):
        try:
            self.get()
        except HTTPError:
            self.create()
        return self

    def delete(self):
        self.knex.delete(self.nested_url())
        self.already_fetched = False
        self.deleted = True
