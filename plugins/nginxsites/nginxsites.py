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
import re
import subprocess
import shutil
from os import path, listdir

import deform

from ninjasysop.backends import Backend, BackendApplyChangesException

from forms import SiteSchema, SiteValidator, CustomSiteSchema
from texts import texts
from datetime import datetime

# SERIAL = yyyymmddnn ; serial
PARSER_RE = {
    'server_name':re.compile(r'server_name *(?:(\w+)|(\w+ *,)+) *;'),
    'proxy_pass':re.compile(r'proxy_pass *(?P<proxy_pass>\w+) *;'),
    'proxy_type':re.compile(r'^# ninjasysop-nginxsites PROXY_PASS$'),
}

RELOAD_COMMAND = "service nginx reload"



class BaseSite(object):
    def __init__(self, name, basedir):
        self.name = name
        self.basedir = basedir
        self.filename = path.join(basedir, 'sites-available', name)
        self.filename_enabled = path.join(basedir, 'sites-enabled', name)
        self.enabled = (path.exists(self.filename) and
                           path.exists(self.filename_enabled))

    def open_file(self, mode='r'):
        return open(self.filename, mode)

    def todict(self):
        return dict(name = self.name,
                    enabled = self.enabled
                    )


class CustomSite(BaseSite):
    def __init__(self, **kwargs):
        super(CustomSite, self).__init__(kwargs['name'],
                                        kwargs['basedir'])
        self.type = 'custom'

    def todict(self):
        tdict = super(CustomSite, self).todict()
        with self.open_file('r') as file:
            tdict['content'] = file.read()
        return tdict


class ProxySite(BaseSite):
    def __init__(self, **kwargs):
        super(ProxySite, self).__init__(kwargs['name'],
                                        kwargs['basedir'])
        self.type = 'proxy'

        # Kwargs or Parse file
        self.ssl = False
        self.server_name = 'algo'
        self.other_names = ['otros']
        self.proxy_to = 'http://192.168.10.10:8080'
        self.proxy_set_header = []

    def todict(self):
        tdict = super(ProxySite, self).todict()
        tdict['type'] = self.type
        tdict['ssl'] = self.ssl
        tdict['server_name'] = self.server_name
        tdict['other_names'] = self.other_names
        tdict['proxy_to'] = self.proxy_to
        tdict['proxy_set_header'] = self.proxy_set_header
        return tdict


class SiteDirectory(object):
    def __init__(self, filename):
        self.basedir = filename

    def readfile(self):
        sites = {}
        # Change this to read sites-available directory
        sitedir = listdir(path.join(self.basedir, 'sites-available'))
        for sitefile in sitedir:
            sites[sitefile] = CustomSite(name=sitefile,
                                         basedir=self.basedir)
        return sites

    def __str_site(self, site):
        site = site.name

    def add_site(self, site):
        with site.file(self.basedir, 'r') as sitefile:
            lines = sitefile.readlines()

        with site.file(self.basedir, 'w') as sitefile:
            sitefile.writelines(lines)

    def save_site(self, old_site, site):
        # TODO write site
        return 
        with site.file(self.basedir, 'w') as sitefile:
            sitefile.writelines(lines)

    def remove_site(self, site):
        sitefile = site.filename(self.basedir)
        sitefile_enable = site.filename_enable(self.basedir)
        # TODO rm sitefile files


class NginxSites(Backend):
    def __init__(self, name, basedir):
        super(NginxSites, self).__init__(name, basedir)
        self.groupname = name
        self.basedir = basedir
        self.sitedirectory = SiteDirectory(basedir)
        self.sites = self.sitedirectory.readfile()

    def del_item(self, name):
        self.SiteDirectory.remove_site(name)
        del self.sites[name]

    def get_item(self, name):
        return self.sites[name]

    def get_items(self, name=None, servername=None, roxy_to=None,
                    name_exact=None):
        filters = []

        if name:
            def filter_name(r):
                return r.name.find(name) >= 0
            filters.append(filter_name)

        if servername:
            def filter_servername(r):
                return r.servername == servername
            filters.append(filter_servername)

        if name_exact:
            def filter_name_exact(r):
                return r.name == name >= 0
            filters.append(filter_name)

        if filters:
            return filter(lambda item: all([f(item) for f in filters]),
                         self.sites.values())
        else:
            return self.sites.values()

    def add_item(self, obj):
        site = Site(name=obj["name"],
                      comment=obj["comment"])
        self.sitedirectory.add_site(site)
        self.items[str(site)] = site

    def save_item(self, old_site, data):

        site = Site(name=data["name"],
                     comment=data["comment"])

        self.sitedirectory.save_record(old_site, site)
        self.items[str(site)] = site

    def freeze_file(self, username):
        # generate a copy of actual file with username.serial extension
        pass

    def apply_changes(self, username):
        cmd=RELOAD_COMMAND
        #save_filename = "%s.%s.%s" % (self.filename, self.serial, username)
        #shutil.copy(self.filename, save_filename)
        try:
            subprocess.check_output("%s %s" % (cmd, self.groupname),
                                    stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError, e:
            raise BackendApplyChangesException(e.output)

    def get_edit_schema(self, name):
        return CustomSiteSchema(validator=SiteValidator(self))

    def get_add_schema(self):
        schema = CustomSiteSchema(validator=SiteValidator(self))
        for field in schema.children:
            if field.name == 'name':
                field.widget = deform.widget.TextInputWidget()
        return CustomSiteSchema(validator=SiteValidator(self))

    @classmethod
    def get_edit_schema_definition(self):
        return CustomSiteSchema

    @classmethod
    def get_add_schema_definition(self):
        return CustomSiteSchema

    @classmethod
    def get_texts(self):
        return texts
