# -*- coding: utf-8 -*-
# Copyright (c) <2012> Antonio Pérez-Aranda Alcaide (ant30) <ant30tx@gmail.com>
#                      Antonio Pérez-Aranda Alcaide (Yaco Sistemas SL) <aperezaranda@yaco.es>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of copyright holders nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL COPYRIGHT HOLDERS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# 
from pyramid.config import Configurator

from pyramid.events import subscriber
from pyramid.events import BeforeRender

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


    identifier_id = 'auth_tkt'
    who_ini_file = global_config['__file__']

    config = Configurator(
        settings=settings,
        root_factory=bootstrap,
    )

    config.include("pyramid_whoauth")

    config.add_static_view('static', 'static/',
                           cache_max_age=86400)
    config.add_static_view('img', 'static/img/',
                           cache_max_age=86400)
    config.add_static_view('deform_static', 'deform:static')

    config.add_route('favicon', 'favicon.ico')
#    config.add_route('login', 'login/')
#    config.add_route('logout', 'logout/')

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

    htpasswd_file = settings.get('ninjasysop.htpasswd')
    config.add_settings(htpasswd=htpasswd_file)

    if not backend:
        ConfigurationError('A backend or backends definition are needed')

    config.scan()

    return config.make_wsgi_app()

