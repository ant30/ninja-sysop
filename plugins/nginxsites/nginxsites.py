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

from forms import SiteSchema, SiteValidator
from texts import texts
from datetime import datetime

# SERIAL = yyyymmddnn ; serial
PARSER_RE = {
    'server_name':re.compile(r'server_name *(?P<server_name>\w+) *;'),
    'proxy_pass':re.compile(r'proxy_pass *(?P<proxy_pass>\w+) *;'),
}

RELOAD_COMMAND = "service nginx reload"



class Site(object):
    def __init__(self, name, enabled, proxy_to='', ssl='', comment=''):
        self.name = name
        self.comment = comment or ''
        self.enabled = enabled
        self.proxy_to = proxy_to
        self.ssl = ssl

    def __str__(self):
        return self.name

    def todict(self):
        return dict(name = self.name,
                    comment = self.comment,
                    enabled = self.enabled
                    )

    def is_enabled(self, basedir):
        return (path.exists(self.filename(basedir)) and
               path.exists(self.filename_enable(basedir)))

    def filename(self, basedir):
        filename = path.join(basedir, 'sites-available', self.name)
        filename += '.conf'
        return filename

    def filename_enable(self, basedir):
        filename = path.join(basedir, 'sites-enabled', self.name)
        filename += '.conf'
        return filename

    def file(self, basedir, mode='r'):
        return open(self.filename(basedir), mode)


class SiteDirectory(object):
    def __init__(self, filename):
        self.basedir = filename

    def readfile(self):
        sites = {}
        # Change this to read sites-available directory
        sitedir = listdir(path.join(self.basedir, 'sites-available'))
        for sitefile in sitedir:
            import ipdb; ipdb.set_trace()
            sitefile
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
    def __init__(self, name, filename):
        super(NginxSites, self).__init__(name, filename)
        self.groupname = name
        self.sitedirectory = SiteDirectory(filename)
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
        return SiteSchema(validator=SiteValidator(self))

    def get_add_schema(self):
        schema = SiteSchema(validator=SiteValidator(self))
        for field in schema.children:
            if field.name == 'name':
                field.widget = deform.widget.TextInputWidget()
        return SiteSchema(validator=SiteValidator(self))

    @classmethod
    def get_edit_schema_definition(self):
        return SiteSchema

    @classmethod
    def get_add_schema_definition(self):
        return SiteSchema

    @classmethod
    def get_texts(self):
        return texts
