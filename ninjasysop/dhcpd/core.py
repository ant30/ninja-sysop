import re
import subprocess

# SERIAL = yyyymmddnn ; serial
PARSER_RE = {
    'partition':re.compile(r"(?P<sub>subnet[^\}]*}) *(?P<hosts>.*)$"),
    'hosts': re.compile(r"host (?P<hostname>[^ ]*) *{ *hardware ethernet (?P<mac>[^\;]*); *fixed-address (?P<ip>[^\;]*)")
}

MATCH_RE_STR = {
    'record':r'^{name} *(?:\d+ *|)(?:IN *|){rtype}',
}

RELOAD_COMMAND = "/etc/init.d/isc-dhcpd-server reload"



class Item(object):
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


class GroupFile(object):
    def __init__(self, filename):
        self.filename = filename

    def readfile(self):
        serial = ''
        items = {}
        with open(self.filename, 'r') as groupfile:
            content = groupfile.read()
            partition = PARSER_RE['partition'].search(content.replace("\n",""))
            if not partition:
                raise IOError("Bad File Format")
            (header, hosts) = partition.groups()
            parsed_hosts = PARSER_RE['hosts'].findall(hosts)
            for (name, mac, ip) in parsed_hosts:
                item = Item(name, mac, ip)
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



class GroupReloadError(Exception):
    pass

class Group(object):
    def __init__(self, groupname, filename):
        self.groupname = groupname
        self.groupfile = GroupFile(filename)
        self.items = self.groupfile.readfile()

    def del_item(self, name):
        self.groupfile.remove_item(self.items[name])
        del self.items[name]

    def get_item(self, name):
        return self.items[name]

    def get_items(self, mac=None, ip=None, name=None,
                        mac_exact=None):
        filters = []

        if name:
            def filter_name(r):
                return r.name.find(name) >= 0
            filters.append(filter_name)

        if mac:
            def filter_type(r):
                return r.type == type
            filters.append(filter_type)

        if ip:
            def filter_target(r):
                return r.ip == ip
            filters.append(filter_target)

        if mac_exact:
            def filter_name_exact(r):
                return r.mac == mac >= 0
            filters.append(filter_mac_exact)

        if filters:
            return filter(lambda item: all([f(item) for f in filters]),
                         self.items.values())
        else:
            return self.items.values()

    def add_item(self, name="", mac="", ip="", comment=""):
        item = Item(name=name,
                    mac=mac,
                    ip=ip,
                    comment=comment)

        self.groupfile.add_item(item)
        self.items[str(item)] = item


    def save_item(self, old_item, name="", mac="", ip="", comment=""):
        item = Item(name=name,
                    mac=mac,
                    ip=ip,
                    comment=comment)

        self.groupfile.save_item(old_item, item)
        self.items[str(old_item)] = item

    def group_reload(self, cmd=RELOAD_COMMAND):
        try:
            subprocess.check_output(cmd,
                                    stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError, e:
            raise GroupReloadError(e.output)
