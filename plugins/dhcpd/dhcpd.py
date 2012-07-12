import re
import subprocess

from ninjasysop.backends import Backend, BackendApplyChangesException
from ninjasysop.validators import IntegrityException
import deform

from texts import texts
from forms import HostSchema, DhcpHostValidator

# SERIAL = yyyymmddnn ; serial
PARSER_RE = {
    'partition':re.compile(r"(?P<sub>subnet[^\}]*}) *(?P<hosts>.*)$"),
    'hosts': re.compile(r"host (?P<hostname>[^ ]*) *{ *hardware ethernet (?P<mac>[^\;]*); *fixed-address (?P<ip>[^\;]*)")
}

MATCH_RE_STR = {
    'record':r'^{name} *(?:\d+ *|)(?:IN *|){rtype}',
}

RELOAD_COMMAND = "/etc/init.d/isc-dhcpd-server reload"



class DhcpHost(object):
    def __init__(self, name, mac, ip, comment=''):
        self.ip = ip
        self.mac = mac
        self.name = name
        self.comment = comment or ''

    def __str__(self):
        return self.name

    def todict(self):
        return dict(name = self.name,
                    mac = self.mac,
                    ip = self.ip,
                    comment = self.comment)


class NetworkFile(object):
    def __init__(self, filename):
        self.filename = filename

    def readfile(self):
        serial = ''
        items = {}
        with open(self.filename, 'r') as networkfile:
            content = networkfile.read()
            partition = PARSER_RE['partition'].search(content.replace("\n",""))
            if not partition:
                raise IOError("Bad File Format")
            (header, hosts) = partition.groups()
            parsed_hosts = PARSER_RE['hosts'].findall(hosts)
            for (name, mac, ip) in parsed_hosts:
                item = DhcpHost(name, mac, ip)
                items[name] = item

        return items

    def __str_item(self, item):
        itemstr = ''
        if item.comment:
            itemstr = "#{0}\n".format(item.comment)

        itemstr += "host {name} {{\n hardware ethernet {mac};\n fixed-address {ip};\n}}\n".format(
                                    name=item.name, mac=item.mac, ip=item.ip)

        return itemstr


    def add_item(self, item):

        with open(self.filename, 'r') as filecontent:

            item_str = self.__str_item(item)
            content = filecontent.read()
            content = content + item_str

        with open(self.filename, 'w') as filecontent:
            filecontent.write(content)


    def save_item(self, old_item, item):

        with open(self.filename, 'r') as filecontent:

            item_str = self.__str_item(item)
            content = filecontent.read()
            content_1 = re.sub(r"host %s [^\{]*{.*[^\}]*} *\n" % (old_item.name),
                    item_str, content)
            if content == content_1:
                raise KeyError("host %s not found" % item.name)
            else:
                content = content_1

        with open(self.filename, 'w') as filecontent:
            filecontent.write(content)

    def remove_item(self, item):
        with open(self.filename, 'r') as filecontent:

            content = filecontent.read()
            content_1 = re.sub(r"host %s [^\{]*{.*[^\}]*} *\n" % (item.name),
                               "", content)
            if content == content_1:
                raise KeyError("host %s not found" % item.name)
            else:
                content = content_1

        with open(self.filename, 'w') as filecontent:
            filecontent.write(content)


class Dhcpd(Backend):

    def __init__(self, name, filename):
        super(Dhcpd, self).__init__(name, filename)
        self.networkfile = NetworkFile(filename)
        self.items = self.networkfile.readfile()

    def del_item(self, name):
        self.networkfile.remove_item(self.items[name])
        del self.items[name]

    def get_item(self, name):
        if name in self.items:
            return self.items[name]
        else:
            return None

    def get_items(self, **kwargs):
        filters = []

        if 'name' in kwargs:
            def filter_name(r):
                return r.name.find(kwargs['name']) >= 0
            filters.append(filter_name)

        if 'mac' in kwargs:
            def filter_mac(r):
                return r.mac == kwargs['mac']
            filters.append(filter_type)

        if 'ip' in kwargs:
            def filter_target(r):
                return r.ip == kwargs['ip']
            filters.append(filter_target)

        if 'name_exact' in kwargs:
            def filter_name_exact(r):
                return r.name == kwargs['name']
            filters.append(filter_name_exact)

        if filters:
            return filter(lambda item: all([f(item) for f in filters]),
                         self.items.values())
        else:
            return self.items.values()


    def add_item(self, obj):
        item = DhcpHost(name=obj['name'],
                    mac=obj['mac'],
                    ip=obj['ip'],
                    #comment=obj['comment'],
                    )

        self.networkfile.add_item(item)
        self.items[str(item)] = item

    def save_item(self, old_item, obj):
        item = DhcpHost(name=obj['name'],
                    mac=obj['mac'],
                    ip=obj['ip'],
                    #comment=obj['comment'],
                    )

        self.networkfile.save_item(old_item, item)
        self.items[str(old_item)] = item

    def get_edit_schema(self, name):
        return HostSchema(validator=DhcpHostValidator(self))

    def get_add_schema(self):
        schema = HostSchema(validator=DhcpHostValidator(self, new=True))
        for field in schema.children:
            if field.name == 'name':
                field.widget = deform.widget.TextInputWidget()
        return schema

    @classmethod
    def get_edit_schema_definition(self):
        return HostSchema

    @classmethod
    def get_add_schema_definition(self):
        return HostSchema

    @classmethod
    def get_texts(self):
        return texts
