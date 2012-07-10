

from deform import Form
import deform
import colander

from deform import Form

from webhelpers.paginate import Page, PageURL_WebOb

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPCreated
from pyramid.security import remember
from pyramid.security import forget

from ninjasysop.layouts import Layouts
from ninjasysop.userdb import UserDB

class GroupViews(Layouts):

    def __init__(self, request):
        self.request = request
        settings = self.request.registry.settings
        if 'backend' in settings:
            self.backend = settings['backend']
        elif 'backends' in settings:
            # get backend name from url
            backend_name = self.request.matchdict['backend']
            self.backend = settings['backends'][backend_name]
        self.static_settings = settings['static_settings']

    @view_config(renderer="templates/group_list.pt", route_name="group_list",
                 permission="view")
    def group_list(self):
        groups = self.static_settings.groups.keys()
        return {"groups": groups}

    @view_config(renderer="templates/group.pt", route_name="group_items",
                 permission="view")
    def group_view(self):
        groupname = self.request.matchdict['groupname']
        page = int(self.request.params['page']) if 'page' in self.request.params else 0
        search = self.request.params['search'] if 'search' in self.request.params else None
        groupfile = self.static_settings.groups[groupname]
        group = self.backend(groupname, groupfile)

        if search:
            items = group.get_items(name=search)
        else:
            items = group.get_items()

        entries = []
        for item in items:
            entries.append({'item':item,
                            'protected': item_is_protected(self.static_settings, groupname, item.name)})

        page_url = PageURL_WebOb(self.request)
        entries = Page(entries, page, url=page_url)

        return {"groupname": groupname,
                "entries": entries,
                }

    @view_config(renderer="templates/item.pt", route_name="item_add",
                 permission="edit")
    def item_add(self):
        groupname = self.request.matchdict['groupname']
        groupfile = self.static_settings.groups[groupname]
        group = self.backend(groupname, groupfile)

        schema = group.get_add_schema()
        form = deform.Form(schema, buttons=('submit',))

        response = {"groupname": groupname,
                    "itemname": "new"}
        response["form"] = form.render()

        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except deform.ValidationFailure, e:
                response['form'] = e.render()
                return response

            if not item_is_protected(self.static_settings, groupname, data['name']):
                group.add_item(**data)
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
        groupfile = self.static_settings.zones[groupname]
        group = self.backend(groupname, zonefile)
        if item_is_protected(self.static_settings, groupname, itemname):
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
        groupfile = self.static_settings.groups[groupname]
        group = self.backend(groupname, groupfile)
        protected = item_is_protected(self.static_settings, groupname, itemname)
        response = {"groupname": groupname,
                    "itemname": itemname}

        if self.request.POST and protected:
            return HTTPForbidden("You can not modify this domain name")

        elif protected:
            response['protected'] = protected
            response['item'] = group.get_item(itemname)
            return response

        schema = group.get_edit_schema(itemname)
        form = deform.Form(schema, buttons=('submit',))

        if self.request.POST:
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except deform.ValidationFailure, e:
                response['form'] = e.render()
                return response
            else:
                group.save_item(group.get_item(itemname), **data)
                response = HTTPFound()
                response.location = self.request.route_url('item',
                                                            groupname=groupname,
                                                            itemname=data['name'])
                return response

        item = group.get_item(itemname)
        response['form'] = form.render(item.todict())
        return response

    @view_config(renderer="templates/applychanges.pt", route_name="group_apply",
                 permission="edit")
    def applychanges(self):
        groupname = self.request.matchdict['groupname']
        try:
            self.backend.apply_changes(groupname)
        except self.backendReloadError, e:
            return {"groupname": groupname,
                    "msg": e.message,
                    }

        return {"groupname": groupname}


    @view_config(renderer="templates/login.pt", context=HTTPForbidden)
    @view_config(renderer="templates/login.pt", route_name="login")
    def login(self):
        request = self.request
        login_url = request.resource_url(request.context, 'login')
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
            userdb = UserDB(self.static_settings.htpasswd_file)
            if userdb.check_password(login, password):
                headers = remember(request, login)
                return HTTPFound(location=came_from,
                                 headers=headers)
            message = 'Failed login'

        return dict(
            page_title="Login",
            message=message,
            url=request.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
            )

    @view_config(route_name="logout")
    def logout(self):
        headers = forget(self.request)
        url = self.request.route_url('login')
        return HTTPFound(location=url, headers=headers)


def item_is_protected(settings, groupname, name):
    return (hasattr(settings, 'protected_names') and
            groupname in settings.protected_names and
            name in settings.protected_names[groupname])


class BaseRestView(object):
    def __init__(self, request):
        self.request = request
        settings = self.request.registry.settings
        if 'backend' in settings:
            self.backend = settings['backend']
        self.static_settings = settings['static_settings']

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
        groups = self.static_settings.groups.keys()
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
        groupfile = self.static_settings.groups[self.groupname]
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
                            'protected': item_is_protected(self.static_settings, self.groupname, item.name)})

        return entries

    @view_config(request_method="PUT", permission="edit")
    def apply_changes(self):
        groupname = self.request.matchdict['groupname']
        try:
            self.backend.apply_changes(groupname)
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
        groupfile = self.static_settings.groups[self.groupname]
        self.group = self.backend(self.groupname, groupfile)
        self.itemname = self.request.matchdict['itemname']

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
        schema = self.group.get_add_schema()
        form = deform.Form(schema, buttons=('submit',))
        controls = self.request.PUT.items()
        try:
            data = form.validate(controls)
        except deform.ValidationFailure, e:
            ## FIXME return errors
            response['form'] = e.render()
            return response

        if item_is_protected(self.static_settings, groupname, data['name']):
            return HTTPForbidden("You can not modify this domain name")

        group.add_item(**data)
        response = HTTPFound()

    @view_config(request_method="POST", permission="edit")
    def post(self):
        protected = item_is_protected(self.static_settings, self.groupname, self.itemname)

        if protected:
            return HTTPForbidden("You can not modify this domain name")

        schema = group.get_edit_schema(self.itemname)
        form = deform.Form(schema, buttons=('submit',))
        controls = self.request.POST.items()
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
        if item_is_protected(self.static_settings, self.groupname, self.itemname):
            raise HTTPForbidden("You can not modify this domain name")

        group.del_item(self.itemname)
        response = HTTPFound()
        return response
