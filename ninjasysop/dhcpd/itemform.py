import re

import colander
import deform

from ninjasysop.validators import name_validator, ip_validator, mac_validator
from core import Item

class ItemForm(colander.MappingSchema):
    name = colander.SchemaNode(colander.String(),
                               validator=name_validator)
    ip = colander.SchemaNode(colander.String(),
                             validator=ip_validator)
    mac = colander.SchemaNode(colander.String(),
                              validator=mac_validator)
#    comment = colander.SchemaNode(colander.String(),
#                                  missing=unicode(""))


class ItemValidator:

    def __init__(self, group):
        self.group = group

    def __call__(self, form, value):
        item = Item(**value)

        item_group = self.group.get_item(item.name)

        # verify IP is not duplicated
        ips = self.group.get_items(ip=item.ip)

        if ((item_group and len(ips) > 0) or
            (item_group is None and
                ((len(ips) == 1 and ips[0].name != item.name) or
                  len(ips) > 1))):
            raise colander.Invalid(form['ip'], "Entry IP already exists in config in item %s" % (ips[0].name))

        ## TODO: verify IP is in correct range taken from header file
