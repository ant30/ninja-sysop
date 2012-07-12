import re
import subprocess
import deform

from ninjasysop.backends import Backend

from forms import EntrySchema, EntryValidator
from texts import texts

# SERIAL = yyyymmddnn ; serial
PARSER_RE = {
    'serial':re.compile(r'(?P<serial>\d{10}) *; *serial'),
    'record':re.compile(r'^(?P<name>(?:[a-zA-Z0-9-.]*|@)) *(?:(?P<weight>\d+)'
                        r' *|)(?:IN *|)(?P<type>A|CNAME)'
                        r' *(?P<target>[a-zA-Z0-9-.]*)'
                        r'(?:(?: *|);(?P<comment>.*)$|)'),
}

MATCH_RE_STR = {
    'record':r'^{name} *(?:\d+ *|)(?:IN *|){rtype}',
    'serial':r'(?P<serial>\d{10}) *; *serial',
}

RELOAD_COMMAND = "/usr/sbin/rndc"



class Item(object):
    def __init__(self, name, type, target, weight=0, comment=''):
        self.name = name
        self.type = type
        self.target = target
        self.weight = weight or 0
        self.comment = comment or ''

    def __str__(self):
        return self.name

    def todict(self):
        return dict(name = self.name,
                    type = self.type,
                    target = self.target,
                    weight = self.weight,
                    comment = self.comment)


class ZoneFile(object):
    def __init__(self, filename):
        self.filename = filename

    def readfile(self):
        serial = None
        names = {}
        with open(self.filename, 'r') as zonefile:
            for line in zonefile.readlines():
                serial_line = PARSER_RE['serial'].search(line)
                if serial_line:
                    serial = serial_line
                    continue
                record_line = PARSER_RE['record'].search(line)
                if record_line:
                    record = Item(**record_line.groupdict())
                    names[str(record)] = record
        return (serial, names)

    def __str_record(self, record):
        recordstr = record.name
        if record.weight:
            recordstr += " {0}".format(str(record.weight))

        recordstr += " {type} {target}".format(type=record.type,
                                              target=record.target)
        if record.comment:
            recordstr += ";{0}".format(record.comment)

        recordstr += '\n'
        return recordstr

    def __str_serial(self, serial):
        return "%s ;serial aaaammdd\n" % serial

    def add_record(self, record):
        with open(self.filename, 'r') as zonefile:
            lines = zonefile.readlines()
            lines.append(self.__str_record(record))

        with open(self.filename, 'w') as zonefile:
            zonefile.writelines(lines)

    def save_record(self, old_record, record):
        match = re.compile(MATCH_RE_STR['record'].format(name=old_record.name,
                                                         rtype=old_record.type))
        zonefile = open(self.filename, 'r')
        lines = zonefile.readlines()
        zonefile.close()
        n = 0
        while n < len(lines) and not match.match(lines[n]):
            n += 1

        if n == len(lines):
            raise(KeyError, "Record %s not found" % record.name)
        else:
            lines[n] = self.__str_record(record)

        zonefile = open(self.filename, 'w')
        print lines
        zonefile.writelines(lines)
        zonefile.close()


    def remove_record(self, record):
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


class Bind9(Backend):
    def __init__(self, name, filename):
        super(Bind9, self).__init__(name, filename)
        self.groupname = name
        self.zonefile = ZoneFile(filename)
        (self.serial, self.items) = self.zonefile.readfile()
        assert self.serial, "ERROR: Serial is undefined on %s" % self.filename

    def del_item(self, name):
        self.zonefile.remove_record(self.items[name])
        del self.items[name]

    def get_item(self, name):
        return self.items[name]

    def get_items(self, name=None, type=None, target=None,
                    name_exact=None):
        filters = []

        if name:
            def filter_name(r):
                return r.name.find(name) >= 0
            filters.append(filter_name)

        if type:
            def filter_type(r):
                return r.type == type
            filters.append(filter_type)

        if target:
            def filter_target(r):
                return r.target == target
            filters.append(filter_target)

        if name_exact:
            def filter_name_exact(r):
                return r.name == name >= 0
            filters.append(filter_name)

        if filters:
            return filter(lambda item: all([f(item) for f in filters]),
                         self.items.values())
        else:
            return self.items.values()

    def add_item(self, obj):
        if obj["name"].endswith(self.groupname):
            entry = obj["name"].replace(".%s" % self.groupname, "")
        elif obj["name"].endswith('.'):
            entry = obj["name"][:-1]
        else:
            entry = obj["name"]

        record = Item(name=entry,
                        type=obj["type"],
                        target=obj["target"],
                        comment=obj["comment"],
                        weight=obj["weight"])

        self.zonefile.add_record(record)
        self.items[str(record)] = record


    def save_item(self, old_record, data):
        if data["name"].endswith(self.groupname):
            entry = data["name"].replace(".%s" % self.groupname, "")
        elif data["name"].endswith('.'):
            entry = data["name"][:-1]
        else:
            entry = data["name"]

        record = Item(name=entry,
                        type=data["type"],
                        target=data["target"],
                        comment=data["comment"],
                        weight=data["weight"])

        self.zonefile.save_record(old_record, record)
        self.items[str(record)] = record



    def __update_serial(self):
        today_str = today.strftime("%Y%m%d")
        if self.serial.startswith(today_str):
            change = self.serial[8:]
            inc_change = int(change) + 1
            serial = long("%s%02d" % (today_str, inc_change))
        else:
            serial = long("%s01" % today_str)
        self.zonefile.save_serial(self.serial)
        self.serial = serial

    def applychanges(self, cmd=RELOAD_COMMAND):
        self.__update_serial()
        try:
            subprocess.check_output("%s reload %s" % (cmd, self.groupname),
                                    stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError, e:
            raise GroupReloadError(e.output)

    def get_edit_schema(self, name):
        return EntrySchema(validator=EntryValidator(self))

    def get_add_schema(self):
        schema = EntrySchema(validator=EntryValidator(self))
        for field in schema.children:
            if field.name == 'name':
                field.widget = deform.widget.TextInputWidget()
        return EntrySchema(validator=EntryValidator(self))

    @classmethod
    def get_edit_schema_definition(self):
        return EntrySchema

    @classmethod
    def get_add_schema_definition(self):
        return EntrySchema

    @classmethod
    def get_texts(self):
        return texts
