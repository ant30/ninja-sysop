import re

import colander
import deform

from ninjasysop.validators import name_validator, ip_validator, mac_validator


class EditHostSchema(colander.MappingSchema):
    ip = colander.SchemaNode(colander.String(),
                             validator=ip_validator)
    mac = colander.SchemaNode(colander.String(),
                              validator=mac_validator)
#    comment = colander.SchemaNode(colander.String(),
#                                  missing=unicode(""))


class AddHostSchema(EditHostSchema):
    name = colander.SchemaNode(colander.String(),
                               validator=name_validator)


class DhcpHostValidator:

    def __init__(self, group):
        self.group = group

    def __call__(self, form, value):
        from dhcpd import DhcpHost
        item = DhcpHost(**value)

        item_group = self.group.get_item(item.name)

        # verify IP is not duplicated
        ips = self.group.get_items(ip=item.ip)

        if ((item_group and len(ips) > 0) or
            (item_group is None and
                ((len(ips) == 1 and ips[0].name != item.name) or
                  len(ips) > 1))):
            #raise colander.Invalid(form['ip'], "Entry IP already exists in config in item %s" % (ips[0].name))


            exc = colander.Invalid(form, 'Entry IP already assigned to host %s' % (ips[0].name))
            exc['ip'] = colander.Invalid(
                  form, "IP repeated, select another ip")
            raise exc

        ## TODO: verify IP is in correct range taken from header file
