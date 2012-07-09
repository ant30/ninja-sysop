import re

import colander
import deform

from ninjasysop.validators import ip_validator

recordtype_choices = (
    ('CNAME', 'CNAME'),
    ('A', 'A'),
)

RE_NAME =  r"^[\w.]+[^.]$"
RE_IP = r"^(?:\d{1,3}\.){3}(?:\d{1,3})$"



class EditEntrySchema(colander.MappingSchema):
    type = colander.SchemaNode(colander.String(),
                    widget=deform.widget.SelectWidget(values=recordtype_choices)
                )
    target = colander.SchemaNode(colander.String())
    weight = colander.SchemaNode(colander.Integer())
    comment = colander.SchemaNode(colander.String(),
                                  missing=unicode(""))


class AddEntrySchema(EditEntrySchema):
    name = colander.SchemaNode(colander.String())


class EntryValidator:

    def __init__(self, group):
        self.group = group

    def __call__(self, form, value):
        from bind9 import Item
        item = Item(**value)
        item_group = self.group.get_item(item.name)

        if item.type == 'A':
            ip_validator(form, item.target)

        elif item.type == 'CNAME':
            if not re.match(RE_NAME, item.target):
                exc = colander.Invalid(form, 'Invalid targe value using A record type')
                exc['target'] = colander.Invalid(
                      form, "A NAME value is required 'ej2' for 'ej2.example.com' ")
                raise exc
