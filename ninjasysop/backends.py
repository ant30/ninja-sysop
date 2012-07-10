import pkg_resources

ENTRYPOINT = 'ninjasysop.plugins'


class BackendApplyChangesException(Exception):
    pass


class Backend(object):

    _shared_states = {}
    def __init__(self, name, filename):
        self.__dict__ = self._shared_states
        self.name = name
        self.filename = filename

    def get_name(self):
        return self.name

    def get_filename(self):
        return self.filename

    def del_item(self, name):
        raise NotImplementedError("Not del_item implemented")

    def get_item(self, name):
        raise NotImplementedError("Not get_item implemented")

    def get_items(self, **kwargs):
        raise NotImplementedError("Not get_items implemented")

    def add_item(self, **kwargs):
        raise NotImplementedError("Not add_item implemented")

    def save_item(self, **kwargs):
        raise NotImplementedError("Not save_item implemented")

    def get_edit_schema(self):
        raise NotImplementedError("Not get_editform implemented")

    def get_add_schema(self, name):
        raise NotImplementedError("Not get_addform implemented")

    def apply_changes(self):
        raise NotImplementedError("Not apply_changes implemented")

    @classmethod
    def get_edit_schema_definition(self):
        raise NotImplementedError("Not edit schema definition implemented")

    @classmethod
    def get_add_schema_definition(self):
        raise NotImplementedError("Not add schema definition implemented")

    @classmethod
    def get_texts(self):
        raise NotImplementedError("Not get_texts implemented")

    @classmethod
    def __unicode__(self):
        return self.__name__


def load_backends():
    Backends = {}
    for entrypoint in pkg_resources.iter_entry_points(ENTRYPOINT):
        backend_class = entrypoint.load()
        Backends[entrypoint.name] = backend_class
    return Backends
