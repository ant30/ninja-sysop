import re
import subprocess

# SERIAL = yyyymmddnn ; serial
PARSER_RE = {
    'partition':re.compile(r"(?P<sub>subnet[^\}]*}) *(?P<hosts>.*)$")
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
        names = {}
        with open(self.filename, 'r') as groupfile:
            content = groupfile.read()
            partition = PARSER_RE['partition'].search(content)
            if not partition:
                raise IOError("Bad File Format")
            (header, hosts) = parition.groups()
            parsed_hosts = PARSER_RE['hosts'].findall(hosts)
            for (name, mac, ip) in parsed_hosts:
                item = Item(name, mac, ip)
                items[name] = Item

        return (serial, items)

    def __str_item(self, item):
        itemstr = ''
        if item.comment:
            itemstr = "#{0}\n".format(item.comment)

        itemstr += "host {name} \{\n hardware ethernet {mac};\n fixed-address {ip}\n}".format(
                                    name=item.name, mac=item.mac, ip=item.ip

        return itemstr

    def save_record(self, item, old_item):
        re.sub("host www([ \n]+)", "host %s", item.name, vlan)

        with open(self.filename, 'r') as filecontent:
            content = filecontent.read()
            content_1 = re.sub("host %s( *){" % old_item.name,
                               "host %s {" % item.name,
                               content)
            if content == content_1:
                raise KeyError("host %s not found" % old_item.name)
            else:
                content = content_1

            content_1 = re.sub("hardware ethernet %s( *);" % old_item.mac,
                               "hardware ethernet %s ;" % item.mac,
                               content)
            if content == content_1:
                raise KeyError("mac %s not found" % old_item.mac)
            else:
                content = content_1

            content_1 = re.sub("fixed-address %s( *);" % old_item.ip,
                               "fixed-address %s ;" % item.ip,
                               content)
            if content == content_1:
                raise KeyError("host %s not found" % old_item.ip)
            else:
                content = content_1

        with open(self.filename, 'w') as filecontent
            filecontent.write(content)

    def remove_record(self, record):
        # TODO
        match = re.compile(MATCH_RE_STR['record'].format(name=record.name,
                                                         rtype=record.type))
        zonefile = open(self.filename, 'r')
        lines = zonefile.readlines()
        zonefile.close()
        n = 0
        while n < len(lines) and not match.match(lines[n]):
            n += 1

        if n == len(lines):
            raise KeyError("Not Found, %s can't be deleted" % record.name)
        else:
            del lines[n]

        zonefile = open(self.filename, 'w')
        zonefile.writelines(lines)
        zonefile.close()

    def save_serial(self, serial):
        # TODO
        match = re.compile(MATCH_RE_STR['serial'])

        zonefile = open(self.filename, 'r')
        lines = zonefile.readlines()
        zonefile.close()

        n = 0
        while n < len(lines) and not match.match(lines[n]):
            if match.match(lines[n]):

                break
            n += 1

        if n == len(lines):
            raise KeyError("Serial not found in file %s" % self.filename)
        else:
            lines[n] = self.__str_serial()

        zonefile = open(self.filename, 'w')
        zonefile.writelines(lines)
        zonefile.close()


class GroupReloadError(Exception):
    pass

class Group(object):
    def __init__(self, groupname, filename):
        self.groupname = groupname
        self.groupfile = GroupFile(filename)

    def del_item(self, name):
        self.groupfile.remove_record(self.items[name])
        del self.items[name]

    def get_item(self, ip):
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
            filters.append(foñter_mac_exact)

        if filters:
            return filter(lambda item: all([f(item) for f in filters]),
                         self.items.values())
        else:
            return self.items.values()

    def add_item(self, name="", type="", target="", comment="", weight=0):
        # TODO
        if name.endswith(self.groupname):
            entry = name.replace(".%s" % self.groupname, "")
        elif name.endswith('.'):
            entry = name[:-1]
        else:
            entry = name

        record = Record(name=entry,
                        type=type,
                        target=target,
                        comment=comment,
                        weight=weight)

        self.groupfile.save_record(record)
        self.items[str(record)] = record

    def group_reload(self, cmd=RELOAD_COMMAND):
        try:
            subprocess.check_output(cmd,
                                    stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError, e:
            raise GroupReloadError(e.output)
