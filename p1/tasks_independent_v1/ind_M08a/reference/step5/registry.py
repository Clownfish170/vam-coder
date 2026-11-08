"""Command registry."""


COMMANDS = {}


ORDER = []


def register(name, fn):
    if name not in COMMANDS:
        ORDER.append(name)
    COMMANDS[name] = fn


class UnknownCommand(Exception):
    pass


ALIASES = {}


def register_alias(alias, target):
    ALIASES[alias] = target


def dispatch(name, arg):
    name = ALIASES.get(name, name)
    if name not in COMMANDS:
        raise UnknownCommand(name)
    out = COMMANDS[name](arg)
    if out is None:
        return "ok"
    return out


def names():
    return list(ORDER)
