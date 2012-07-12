from pyramid.config import Configurator

from pyramid.events import subscriber
from pyramid.events import BeforeRender

from pyramid.authentication import AuthTktAuthenticationPolicy

from resources import bootstrap
from pyramid.exceptions import ConfigurationError, NotFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import append_slash_notfound_view

from backends import load_backends


def add_global_texts(backend):
    def events(event):
        event['texts'] = backend.get_texts()
    return events

def notfound(request):
    return HTTPNotFound('Not found')


def get_protected_names(settings):
    raw = settings.get('ninjasysop.protected_names', None)
    if raw is None:
        raise ConfigurationError("Not protected_names set")

    protected = {}
    for item in raw.split('\n'):
        if not item:
            continue
        name, protected_names_raw = item.split(':')
        protected[name] = protected_names_raw.split(',')

    return protected

def get_files(settings):
    raw = settings.get('ninjasysop.files', None)
    if raw is None:
        raise ConfigurationError("Not config files set")

    files = {}
    for item in raw.split('\n'):
        if not item:
            continue
        name, filename = item.split(':')
        files[name] = filename

    return files


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(
        settings=settings,
        root_factory=bootstrap,
        authentication_policy=AuthTktAuthenticationPolicy(
            'seekr1t'),
    )

    config.add_static_view('static', 'static/',
                           cache_max_age=86400)
    config.add_static_view('img', 'static/img/',
                           cache_max_age=86400)
    config.add_static_view('deform_static', 'deform:static')

    config.add_route('favicon', 'favicon.ico')
    config.add_route('login', 'login/')
    config.add_route('logout', 'logout/')

    config.add_route('backend_rest_view','api/')
    config.add_route('backend_rest_edit_schema', 'api/schema/edit/')
    config.add_route('backend_rest_add_schema', 'api/schema/add/')
    config.add_route('group_rest_view', 'api/{groupname}/')
    config.add_route('item_rest_view', 'api/{groupname}/{itemname}/')

    config.add_route('group_items', '{groupname}/')
    config.add_route('group_apply', '{groupname}/applychanges/')
    config.add_route('item_add', '{groupname}/add/')
    config.add_route('item', '{groupname}/{itemname}/')
    config.add_route('item_delete', '{groupname}/{itemname}/delete/')

    config.add_route('group_list', '')

    config.add_view(append_slash_notfound_view, context=NotFound)

    backend_name = settings.get('ninjasysop.backend')

    allbackends = load_backends()
    backend = allbackends[backend_name]
    config.add_settings(backend=backend)
    config.add_subscriber(add_global_texts(backend), BeforeRender)

    files=get_files(settings)
    protected_names = get_protected_names(settings)
    for key in files.keys():
        if key not in protected_names:
            protected_names[key] = []
    config.add_settings(files=files)
    config.add_settings(protected_names=protected_names)


    if not backend:
        ConfigurationError('A backend or backends definition are needed')

    config.scan()

    return config.make_wsgi_app()

