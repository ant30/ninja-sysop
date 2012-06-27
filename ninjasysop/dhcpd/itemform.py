import re

import colander
import deform

from ninjasysop.validators import name_validator, ip_validator, mac_validator

class ItemForm(colander.MappingSchema):
    name = colander.SchemaNode(colander.String(),
                               validator=name_validator)
    ip = colander.SchemaNode(colander.String(),
                             validator=ip_validator)
    mac = colander.SchemaNode(colander.String(),
                              validator=mac_validator)
#    comment = colander.SchemaNode(colander.String(),
#                                  missing=unicode(""))


def item_validator(form, value):
    pass
