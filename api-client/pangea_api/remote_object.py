
from requests.exceptions import HTTPError


class RemoteObjectError(Exception):
    pass


class RemoteObjectOverwriteError(RemoteObjectError):
    pass


class RemoteObject:

    def __init__(self, *args, **kwargs):
        self._already_fetched = False
        self._modified = False
        self._deleted = False
        self.blob = None

    def __setattr__(self, key, val):
        if hasattr(self, 'deleted') and self._deleted:
            raise RemoteObjectError('This object has been deleted.')
        super(RemoteObject, self).__setattr__(key, val)
        if key in self.remote_fields or key == self.parent_field:
            super(RemoteObject, self).__setattr__('_modified', True)

    def load_blob(self, blob):
        if self._deleted:
            raise RemoteObjectError('This object has been deleted.')
        for field in self.remote_fields:
            current = getattr(self, field, None)
            try:
                new = blob[field]
            except KeyError:
                raise KeyError(f'Key {field} is missing for object {self} (type {type(self)}) in blob: {blob}')
            if current and current != new:
                is_overwrite = True
                if isinstance(current, dict) and isinstance(new, dict):
                    append_only = True
                    for k, v in current.items():
                        if (k not in new) or (new[k] != v):
                            append_only = False
                        break
                    if append_only:
                        is_overwrite = False
                if is_overwrite:
                    raise RemoteObjectOverwriteError((
                        f'Loading blob would overwrite field "{field}":\n\t'
                        f'current: "{current}" (type: "{type(current)}")\n\t'
                        f'new: "{new}" (type: "{type(new)}")'
                    ))
            setattr(self, field, new)

    def get(self):
        """Fetch the object from the server."""
        if self._deleted:
            raise RemoteObjectError('This object has been deleted.')
        if not self._already_fetched:
            self._get()
            self._already_fetched = True
            self._modified = False
        return self

    def create(self):
        """Create this object on the server."""
        if self._deleted:
            raise RemoteObjectError('This object has been deleted.')
        if not self._already_fetched:
            self._create()
            self._already_fetched = True
            self._modified = False
        return self

    def save(self):
        """Assuming the object exists on the server make the server-side object
        match the state of this object.
        """
        if self._deleted:
            raise RemoteObjectError('This object has been deleted.')
        if not self._already_fetched:
            msg = 'Attempting to SAVE an object which has not been fetched is disallowed.'
            raise RemoteObjectError(msg)
        if self._modified:
            self._save()
            self._modified = False

    def idem(self):
        """Make the state of this object match the server."""
        if self._deleted:
            raise RemoteObjectError('This object has been deleted.')
        if not self._already_fetched:
            try:
                self.get()
            except HTTPError:
                self.create()
        else:
            self.save()
        return self

    def delete(self):
        self.knex.delete(self.nested_url())
        self._already_fetched = False
        self._deleted = True
