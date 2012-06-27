from colander import Invalid
import re

RE_IP = re.compile(r"^(?:\d{1,3}\.){3}(?:\d{1,3})$")

RE_NAME = re.compile(r"^([a-z0-9]([-a-z0-9]*[a-z0-9])?\\.)*([a-z0-9]+)$", re.IGNORECASE)

RE_MAC = re.compile(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", re.IGNORECASE)


def ip_validator(node, value):
    if RE_IP.match(value) is None:
        raise Invalid(node, "%s is not a valid IP" % value)


def name_validator(node, value):
    if RE_NAME.match(value) is None:
        raise Invalid(node, "%s is not a valid Name, valid caracters are [-a-zA-Z0-9], and not ends with on '.' " % value)


def mac_validator(node, value):
    if RE_MAC.match(value) is None:
        raise Invalid(node, "%s is not a valid MAC (AA:FF:cc:00:11:22) " % value)
