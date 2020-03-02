

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

    def idem(self):
        try:
            self.get()
        except:
            self.create()
