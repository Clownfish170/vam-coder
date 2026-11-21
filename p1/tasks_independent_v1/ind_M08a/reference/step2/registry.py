"""Command registry."""


COMMANDS = {}


def register(name, fn):
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
    return COMMANDS[name](arg)


def names():
    return sorted(COMMANDS)
