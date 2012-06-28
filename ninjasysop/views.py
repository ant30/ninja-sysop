

from deform import Form
import deform
import colander

from deform import ZPTRendererFactory
from deform import Form
from pkg_resources import resource_filename


from webhelpers.paginate import Page, PageURL_WebOb

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPCreated
from pyramid.security import remember
from pyramid.security import forget

from ninjasysop.layouts import Layouts
from ninjasysop.userdb import UserDB
from ninjasysop import settings

from ninjasysop.backend import itemform, core


class GroupViews(Layouts):

    def __init__(self, request):
        self.request = request

    @view_config(renderer="templates/group_list.pt", route_name="group_list",
                 permission="view")
    def group_list(self):
        groups = settings.groups.keys()
        return {"groups": groups}

    @view_config(renderer="templates/group.pt", route_name="group_items",
                 permission="view")
    def group_view(self):
        groupname = self.request.matchdict['groupname']
        page = int(self.request.params['page']) if 'page' in self.request.params else 0
        search = self.request.params['search'] if 'search' in self.request.params else None
        groupfile = settings.groups[groupname]
        group = core.Group(groupname, groupfile)

        if search:
            items = group.get_items(name=search)
        else:
            items = group.get_items()

        entries = []
        for item in items:
            entries.append({'item':item,
                            'protected': item_is_protected(groupname, item.name)})

        page_url = PageURL_WebOb(self.request)
        entries = Page(entries, page, url=page_url)

        return {"groupname": groupname,
                "entries": entries,
                }

    @view_config(renderer="templates/item.pt", route_name="item_add",
                 permission="edit")
    def item_add(self):
        groupname = self.request.matchdict['groupname']
        groupfile = settings.groups[groupname]
        group = core.Group(groupname, groupfile)

        schema = itemform.ItemForm(validator=itemform.ItemValidator(group))
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

            if not item_is_protected(groupname, data['name']):
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
        groupfile = settings.zones[groupname]
        group = core.Group(groupname, zonefile)
        if item_is_protected(groupname, itemname):
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
        groupfile = settings.groups[groupname]
        group = core.Group(groupname, groupfile)
        protected = item_is_protected(groupname, itemname)
        response = {"groupname": groupname,
                    "itemname": itemname}

        if self.request.POST and protected:
            return HTTPForbidden("You can not modify this domain name")

        elif protected:
            response['protected'] = protected
            response['item'] = group.get_item(itemname)
            return response



        schema = itemform.ItemForm(validator=itemform.ItemValidator(group))
        form = deform.Form(schema, buttons=('submit',))
        form['name'].widget = deform.widget.HiddenWidget()

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
            group_reload_signal(groupname, get_rndc_command())
        except core.GroupReloadError, e:
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
            userdb = UserDB(settings.htpasswd_file)
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


def item_is_protected(groupname, name):
    return (hasattr(settings, 'protected_names') and
            groupname in settings.protected_names and
            name in settings.protected_names[groupname])
