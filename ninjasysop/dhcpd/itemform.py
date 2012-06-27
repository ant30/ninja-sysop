import re

import colander
import deform

recordtype_choices = (
    ('CNAME', 'CNAME'),
    ('A', 'A'),
)

RE_IP = r"^(?:\d{1,3}\.){3}(?:\d{1,3})$"
RE_NAME =  r"^[\w.]+[^.]$"


class ItemForm(colander.MappingSchema):
    name = colander.SchemaNode(colander.String())
    ip = colander.SchemaNode(colander.String())
    mac = colander.SchemaNode(colander.String())
    comment = colander.SchemaNode(colander.String(),
                                  missing=unicode(""))


def item_validator(form, value):
    pass
