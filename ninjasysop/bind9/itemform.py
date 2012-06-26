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
    type = colander.SchemaNode(colander.String(),
                    widget=deform.widget.SelectWidget(values=recordtype_choices)
                )
    target = colander.SchemaNode(colander.String())
    weight = colander.SchemaNode(colander.Integer())
    comment = colander.SchemaNode(colander.String(),
                                  missing=unicode(""))


def item_validator(form, value):
    if value['type'] == 'A':
        if not re.match(RE_IP, value['target']):
            exc = colander.Invalid(form, 'Invalid targe value using A record type')
            exc['target'] = colander.Invalid(
                  form, "A IP value is required (255.255.255.255)")
            raise exc

    elif value['type'] == 'CNAME':
        if not re.match(RE_NAME, value['target']):
            exc = colander.Invalid(form, 'Invalid targe value using A record type')
            exc['target'] = colander.Invalid(
                  form, "A NAME value is required 'ej2' for 'ej2.example.com' ")
            raise exc
