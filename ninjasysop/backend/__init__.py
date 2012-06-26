import imp
from ninjasysop import settings

def import_(module_name, app=settings.app):
    file, filename, data = imp.find_module('ninjasysop/%s/%s' % (app,
                                                                 module_name))
    mod = imp.load_module(module_name, file, filename, data)
    return mod


core = import_('core')
itemform = import_('itemform')
texts = import_('texts')

__all__ = ["core", "itemform", "texts"]
