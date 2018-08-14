import base64
import codecs
import string
import yaml


version = '0.1.0'


def get_version():
    return '0.1.0'


def get_section_path(section, input_separator):
    section_path = []
    if section is not None:
        _steps = section.split(input_separator)
        for s in _steps:
            if len(s):
                section_path.append(s)
    return section_path


def get_parameter_path(parameter, input_separator):
    return get_section_path(parameter, input_separator)


# ----------------------------------------------------------------------
# R13
#


class B64(str):
    def __new__(cls, s):
        s64 = base64.b64encode(s)
        return str.__new__(cls, s64)

    def __repr__(self):
        return "B64(%s)" % self

    # @classmethod
    def decode(self):
        return base64.b64decode(self)


def b64_representer(dumper, data):
    return dumper.represent_scalar(u'!b64', u'%s' % data)

yaml.add_representer(B64, b64_representer)


def b64_constructor(loader, node):
    value = loader.construct_scalar(node)
    return B64(base64.b64decode(value))

yaml.add_constructor(u'!b64', b64_constructor)


# ----------------------------------------------------------------------
# R13
#


class R13(str):
    def __new__(cls, s):
        rot13 = string.maketrans(
            "ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz",
            "NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm",
        )
        # return str.__new__(cls, string.translate(s, rot13))
        return str.__new__(cls, codecs.encode(s, 'rot_13'))

    def __repr__(self):
        return "R13(%s)" % self

    # @classmethod
    def decode(self):
        unrot13 = str.maketrans(
            "NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm",
            "ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz",
        )
        value = "%s" % self
        return value.decode('rot_13')


def r13_representer(dumper, data):
    return dumper.represent_scalar(u'!r13', u'%s' % data)

yaml.add_representer(R13, r13_representer)


def r13_constructor(loader, node):
    value = loader.construct_scalar(node)
    unrot13 = str.maketrans(
        "NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm",
        "ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz",
    )
    # return str.translate(value, unrot13)
    return value.decode('rot_13')

yaml.add_constructor(u'!r13', b64_constructor)


# ----------------------------------------------------------------------
# Vault
#


class Vault(str):
    """ A subtype of str """

    def __new__(cls, s):
        s64 = base64.b64encode(s)
        return str.__new__(cls, s64)

    def __repr__(self):
        return "Vault(%s)" % self

    # @classmethod
    def decode(self):
        return base64.b64decode(self)


def vault_representer(dumper, data):
    return dumper.represent_scalar(u'!vault', u'%s' % data)

yaml.add_representer(Vault, vault_representer)


def vault_constructor(loader, node):
    value = loader.construct_scalar(node)
    return Vault(base64.b64decode(value))

yaml.add_constructor(u'!vault', vault_constructor)
