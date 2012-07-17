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

import colander
import deform

from ninjasysop.validators import name_validator, ip_validator, mac_validator

from ipaddr import IPv4Address


class HostSchema(colander.MappingSchema):
    name = colander.SchemaNode(
                colander.String(),
                validator=name_validator,
                widget = deform.widget.HiddenWidget(),
                )
    ip = colander.SchemaNode(colander.String(),
                             validator=ip_validator)
    mac = colander.SchemaNode(colander.String(),
                              validator=mac_validator)
#    comment = colander.SchemaNode(colander.String(),
#                                  missing=unicode(""))



class DhcpHostValidator:

    def __init__(self, group, new=False):
        self.group = group
        self.new = new

    def __call__(self, form, value):
        from dhcpd import DhcpHost
        item = DhcpHost(**value)


        if self.new:
            item_group = self.group.get_item(item.name)
            if item_group:
                exc = colander.Invalid(form, 'Entry Host already exist')
                exc['name'] = colander.Invalid(
                      form, "Entry host already exist")
                raise exc

        # verify IP is not duplicated
        ips = self.group.get_items(ip=item.ip)

        if ((self.new and len(ips) > 0 ) or
            (not self.new and len(ips) == 1 and ips[0].name != item.name)):
            exc = colander.Invalid(form, 'Entry IP already assigned to host %s' % (ips[0].name))
            exc['ip'] = colander.Invalid(
                  form, "IP is already assigned, select another ip")
            raise exc

        ## TODO: verify IP is in correct range taken from header file
        if IPv4Address(item.ip) not in self.group.network['network']:
            exc = colander.Invalid(form, '%s is not a valid IP' % (item.ip))
            exc['ip'] = colander.Invalid(
                  form, "This IP is not a valid IP")
            raise exc

