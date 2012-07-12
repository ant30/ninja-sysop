import re

import colander
import deform

from ninjasysop.validators import name_validator, ip_validator, mac_validator


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
