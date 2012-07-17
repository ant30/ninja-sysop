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
import pkg_resources

ENTRYPOINT = 'ninjasysop.plugins'


class BackendApplyChangesException(Exception):
    pass


class Backend(object):

    _shared_states = {}
    def __init__(self, name, filename):
        self.__dict__ = self._shared_states
        self.name = name
        self.filename = filename

    def get_name(self):
        return self.name

    def get_filename(self):
        return self.filename

    def del_item(self, name):
        raise NotImplementedError("Not del_item implemented")

    def get_item(self, name):
        raise NotImplementedError("Not get_item implemented")

    def get_items(self, **kwargs):
        raise NotImplementedError("Not get_items implemented")

    def add_item(self, **kwargs):
        raise NotImplementedError("Not add_item implemented")

    def save_item(self, **kwargs):
        raise NotImplementedError("Not save_item implemented")

    def get_edit_schema(self):
        raise NotImplementedError("Not get_editform implemented")

    def get_add_schema(self, name):
        raise NotImplementedError("Not get_addform implemented")

    def apply_changes(self, username):
        raise NotImplementedError("Not apply_changes implemented")

    @classmethod
    def get_edit_schema_definition(self):
        raise NotImplementedError("Not edit schema definition implemented")

    @classmethod
    def get_add_schema_definition(self):
        raise NotImplementedError("Not add schema definition implemented")

    @classmethod
    def get_texts(self):
        raise NotImplementedError("Not get_texts implemented")

    @classmethod
    def __unicode__(self):
        return self.__name__


def load_backends():
    Backends = {}
    for entrypoint in pkg_resources.iter_entry_points(ENTRYPOINT):
        backend_class = entrypoint.load()
        Backends[entrypoint.name] = backend_class
    return Backends
