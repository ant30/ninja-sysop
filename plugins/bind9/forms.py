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



class EntrySchema(colander.MappingSchema):
    name = colander.SchemaNode(
                colander.String(),
                widget = deform.widget.HiddenWidget(),
                )
    type = colander.SchemaNode(colander.String(),
                    widget=deform.widget.SelectWidget(values=recordtype_choices)
                )
    target = colander.SchemaNode(colander.String())
    weight = colander.SchemaNode(colander.Integer(),
                                 missing=0)
    comment = colander.SchemaNode(colander.String(),
                                  missing=unicode(""))


class EntryValidator:

    def __init__(self, group, new=False):
        self.group = group
        self.new = False

    def __call__(self, form, value):
        from bind9 import Item
        item = Item(**value)
        item_group = self.group.get_items(name=item.name)

        if ((self.new and len(item_group) > 0) or
            (not self.new and len(item_group) > 1)):
                exc = colander.Invalid(form, 'Invalid name, it already exist')
                exc['target'] = colander.Invalid(
                        form, "This name is already exist")
                raise exc

        if item.type == 'A':
            ip_validator(form, item.target)

        elif item.type == 'CNAME':
            if not re.match(RE_NAME, item.target):
                exc = colander.Invalid(form, 'Invalid targe value using A record type')
                exc['target'] = colander.Invalid(
                      form, "A NAME value is required 'ej2' for 'ej2.example.com' ")
                raise exc
