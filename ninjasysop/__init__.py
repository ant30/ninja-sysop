from pyramid.config import Configurator

from pyramid.events import BeforeRender
from pyramid.authentication import AuthTktAuthenticationPolicy

from resources import bootstrap

#from backend import texts

texts=dict(
    subapp_label = u'Dhcpd range',
    group_label = u'Dhcpd',
    item_label = u'Host',
    item_list_extra_fields = (('mac', u'Mac'),
                              ('ip', u'IP'),
                             )
)

def renderer_globals_factory(system):
    return {'texts': texts.texts}

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(
        settings=settings,
        root_factory=bootstrap,
        authentication_policy=AuthTktAuthenticationPolicy(
            'seekr1t'),
        renderer_globals_factory=renderer_globals_factory
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

    config.scan()

    return config.make_wsgi_app()
