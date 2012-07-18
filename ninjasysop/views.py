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


from deform import Form
import deform
import colander

from deform import Form

from webhelpers.paginate import Page, PageURL_WebOb

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPCreated
from pyramid.security import remember
from pyramid.security import forget
from pyramid.security import authenticated_userid

from ninjasysop.layouts import Layouts
from ninjasysop.userdb import UserDB

from backends import BackendApplyChangesException

class GroupViews(Layouts):

    def __init__(self, request):
        self.request = request
        settings = self.request.registry.settings
        if 'backend' in settings:
            self.backend = settings['backend']
        self.files = settings['files']
        self.protected_names = settings['protected_names']
        self.settings = settings

    @view_config(renderer="templates/group_list.pt", route_name="group_list",
                 permission="view")
    def group_list(self):
        groups = self.files.keys()
        return {"groups": groups}

    @view_config(renderer="templates/group.pt", route_name="group_items",
                 permission="view")
    def group_view(self):
        groupname = self.request.matchdict['groupname']
        page = int(self.request.params['page']) if 'page' in self.request.params else 0
        search = self.request.params['search'] if 'search' in self.request.params else None
        groupfile = self.files[groupname]
        group = self.backend(groupname, groupfile)

        if search:
            items = group.get_items(name=search)
        else:
            items = group.get_items()

        entries = []
        for item in items:
            entries.append({'item':item,
                            'protected':  item.name in self.protected_names[groupname]})

        page_url = PageURL_WebOb(self.request)
        entries = Page(entries, page, url=page_url)

        return {"groupname": groupname,
                "entries": entries,
                }

    @view_config(renderer="templates/item.pt", route_name="item_add",
                 permission="edit")
    def item_add(self):
        groupname = self.request.matchdict['groupname']
        groupfile = self.files[groupname]
        group = self.backend(groupname, groupfile)

        schema = group.get_add_schema()
        form = deform.Form(schema, buttons=('submit',))

        response = {"groupname": groupname,
                    "itemname": "new"}
        response["form"] = form.render()

        if 'submit' in self.request.POST and self.request.POST['submit'] == 'submit':
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except deform.ValidationFailure, e:
                response['form'] = e.render()
                return response

            if data['name'] not in self.protected_names[groupname]:
                group.add_item(data)
                response = HTTPFound()
                response.location = self.request.route_url('item',
                                                            groupname=groupname,
                                                            itemname=data['name'])
                return response
            else:
                return HTTPForbidden()

        return response


    @view_config(route_name="item_delete",
                 permission="edit")
    def item_delete(self):
        groupname = self.request.matchdict['groupname']
        itemname = self.request.matchdict['itemname']
        groupfile = self.files[groupname]
        group = self.backend(groupname, groupfile)
        if itemname in self.protected_names[groupname]:
            raise HTTPForbidden("You can not modify this domain name")

        group.del_item(itemname)
        response = HTTPFound()
        response.location = self.request.route_url('groupview',
                                                    groupname=groupname)
        return response

    @view_config(renderer="templates/item.pt", route_name="item",
                 permission="edit")
    def item_edit(self):
        groupname = self.request.matchdict['groupname']
        itemname = self.request.matchdict['itemname']
        groupfile = self.files[groupname]
        group = self.backend(groupname, groupfile)
        protected = itemname in self.protected_names[groupname]
        response = {"groupname": groupname,
                    "itemname": itemname,
                    'item': group.get_item(itemname),
                    }
        if self.request.POST and protected:
            return HTTPForbidden("You can not modify this domain name")

        elif protected:
            response['protected'] = protected
            return response


        schema = group.get_edit_schema(itemname)
        form = deform.Form(schema, buttons=('submit', 'delete'))

        if 'submit' in self.request.POST and self.request.POST['submit'] == 'submit':
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except deform.ValidationFailure, e:
                response['form'] = e.render()
                return response
            else:
                group.save_item(group.get_item(itemname), data)
                texts = group.get_texts()
                response['flash'] = '%s %s saved' % (texts['item_label'], itemname)

        item = group.get_item(itemname)
        response['form'] = form.render(item.todict())
        return response

    @view_config(renderer="templates/applychanges.pt", route_name="group_apply",
                 permission="edit")
    def applychanges(self):
        groupname = self.request.matchdict['groupname']
        groupfile = self.files[groupname]
        group = self.backend(groupname, groupfile)
        username = authenticated_userid(self.request)
        try:
            group.apply_changes(username)
        except BackendApplyChangesException, e:
            return {"groupname": groupname,
                    "msg": e.message,
                    }

        return {"groupname": groupname}


    @view_config(renderer="templates/login.pt", context=HTTPForbidden)
    @view_config(renderer="templates/login.pt", route_name="login")
    def login(self):
        request = self.request
        login_url = request.resource_url(request.context, 'login')
        login_url += '/'
        referrer = request.url
        if referrer == login_url:
            referrer = '/' # never use the login form itself as came_from
        came_from = request.params.get('came_from', referrer)
        message = ''
        login = ''
        password = ''
        if self.request.POST:
            login = request.params['login']
            password = request.params['password']
            userdb = UserDB(self.settings['htpasswd'])
            if userdb.check_password(login, password):
                headers = remember(request, login)
                return HTTPFound(location=came_from,
                                 headers=headers)
            message = 'Failed login'

        return dict(
            page_title="Login",
            message=message,
            url=request.application_url + '/login/',
            came_from=came_from,
            login=login,
            password=password,
            )

    @view_config(route_name="logout")
    def logout(self):
        headers = forget(self.request)
        url = self.request.route_url('login')
        return HTTPFound(location=url, headers=headers)


class BaseRestView(object):
    def __init__(self, request):
        self.request = request
        settings = self.request.registry.settings
        self.backend = settings['backend']
        self.files = settings['files']
        self.protected_names = settings['protected_names']

    def _serializer(self, schema):
        schema_definition = []
        form = deform.Form(schema())
        for node in form.children:
            schema_node = {'name':  node.name,
                           'required': node.required}
            if isinstance(node.typ, colander.String):
                if getattr(node.widget, 'values', None):
                    schema_node['type'] = [key for (key, value) in node.widget.values]
                else:
                    schema_node['type'] = 'string'
            elif isinstance(node.typ, colander.Integer):
                schema_node['type'] = 'integer'

            schema_definition.append(schema_node)

        return schema_definition

    def _serialize_item(self, item, group):
        schema = self._serializer(group.get_add_schema)
        obj = {}
        for prop in schema:
            obj[prop['name']] = getattr(item, prop['name'], None)
        return obj


@view_defaults(route_name="backend_rest_view", renderer="json", permission="view")
class BackendRestViews(BaseRestView):

    @view_config(renderer="string", request_method="OPTIONS")
    def options(self):
        headers = self.request.response.headers
        headers['Access-Control-Allow-Methods'] = 'GET'
        headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept'
        return ''

    @view_config(request_method="GET")
    def get(self):
        groups = self.files.keys()
        return groups

    @view_config(route_name="backend_rest_edit_schema", request_method="GET")
    def edit_schema(self):
        edit_schema = self._serializer(self.backend.get_edit_schema_definition())
        return edit_schema

    @view_config(route_name="backend_rest_add_schema", request_method="GET")
    def add_schema(self):
        add_schema = self._serializer(self.backend.get_add_schema_definition())
        return add_schema


@view_defaults(route_name="group_rest_view", renderer="json", permission="view")
class GroupRESTViews(BaseRestView):

    def __init__(self, request):
        super(GroupRESTViews, self).__init__(request)
        self.groupname = self.request.matchdict['groupname']
        groupfile = self.files[self.groupname]
        self.group = self.backend(self.groupname, groupfile)

    @view_config(renderer="string", request_method="OPTIONS")
    def options(self):
        headers = self.request.response.headers
        headers['Access-Control-Allow-Methods'] = 'GET, PUT'
        headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept'
        return ''

    @view_config(request_method="GET")
    def get(self):
        search = self.request.params['search'] if 'search' in self.request.params else None

        if search:
            items = self.group.get_items(name=search)
        else:
            items = self.group.get_items()

        entries = []
        for item in items:
            entries.append({'item':self._serialize_item(item, self.group),
                            'protected': item.name in self.protected_names[self.groupname]})

        return entries

    @view_config(request_method="PUT", permission="edit")
    def apply_changes(self):
        groupname = self.request.matchdict['groupname']
        try:
            self.backend.apply_changes(groupname, username)
        except self.backendReloadError, e:
            return {"groupname": groupname,
                    "msg": e.message,
                    }

        return ''

@view_defaults(route_name="item_rest_view", renderer="json", permission="view")
class ItemRESTView(BaseRestView):

    def __init__(self, request):
        super(ItemRESTView, self).__init__(request)
        self.groupname = self.request.matchdict['groupname']
        groupfile = self.files[self.groupname]
        self.group = self.backend(self.groupname, groupfile)
        self.itemname = self.request.matchdict['itemname']
        self.is_protected = self.itemname in self.protected_names[self.groupname]

    @view_config(renderer="string", request_method="OPTIONS")
    def options(self):
        headers = self.request.response.headers
        headers['Access-Control-Allow-Methods'] = 'GET, PUT, POST'
        headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept'
        return ''

    @view_config(request_method="GET", permission="edit")
    def get(self):
        item = self.group.get_item(self.itemname)
        return self._serialize_item(item, self.group)

    @view_config(request_method="PUT", permission="edit")
    def put(self):
        if self.is_protected:
            return HTTPForbidden("You can not modify this domain name")
        schema = self.group.get_add_schema()
        form = deform.Form(schema, buttons=('submit',))
        controls = self.request.PUT.items()
        try:
            data = form.validate(controls)
        except deform.ValidationFailure, e:
            ## FIXME return errors
            response['form'] = e.render()
            return response

        if data['name'] in self.protected_names[self.groupname]:
            return HTTPForbidden("You can not modify this domain name")

        group.add_item(**data)
        response = HTTPFound()

    @view_config(request_method="POST", permission="edit")
    def post(self):

        if self.is_protected:
            return HTTPForbidden("You can not modify this domain name")

        schema = group.get_edit_schema(self.itemname)
        form = deform.Form(schema, buttons=('submit',))
        controls = self.request.POST.items()
        controls.append((u'name', itemname))
        try:
            data = form.validate(controls)
        except deform.ValidationFailure, e:
            ## FIXME error response
            response['form'] = e.render()
            return response
        else:
            group.save_item(group.get_item(self.itemname), **data)
            response = HTTPFound()
            return response

        return response

    @view_config(request_method="DELETE",  permission="edit")
    def delete(self):
        if self.is_protected:
            raise HTTPForbidden("You can not modify this domain name")

        group.del_item(self.itemname)
        response = HTTPFound()
        return response
