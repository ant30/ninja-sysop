from pyramid.config import Configurator

from pyramid.events import subscriber
from pyramid.events import BeforeRender

from pyramid.authentication import AuthTktAuthenticationPolicy

from resources import bootstrap
from pyramid.exceptions import ConfigurationError

#from backend import texts

from backends import load_backends

allbackends = load_backends()
backend = allbackends['Bind9']

@subscriber(BeforeRender)
def add_global(event):
    event['texts'] = backend.get_texts()


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
    config.add_route('login', 'login')
    config.add_route('logout', 'logout')
    config.add_route('group_items', '{groupname}')
    config.add_route('group_apply', '{groupname}/applychanges')
    config.add_route('item_add', '{groupname}/add')
    config.add_route('item', '{groupname}/{itemname}')
    config.add_route('item_delete', '{groupname}/{itemname}/delete')

    config.add_route('group_list', '')

    config.add_settings(backend=backend)

    if not backend:
        ConfigurationError('A backend or backends definition are needed')



    config.scan()

    return config.make_wsgi_app()
