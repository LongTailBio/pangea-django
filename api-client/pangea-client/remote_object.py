

class RemoteObject:

    def __init__(self, *args, **kwargs):
        self.already_fetched = False

    def get(self):
        if not self.already_fetched:
            self._get()
        self.already_fetched = True

    def create(self):
        if not self.already_fetched:
            self._create()
        self.already_fetched = True

    def load_blob(self, blob):
        self.uuid = blob['uuid']
        self.created_at = blob['created_at']
        self.updated_at = blob['updated_at']

    def idem(self):
        try:
            self.get()
        except:
            self.create()
