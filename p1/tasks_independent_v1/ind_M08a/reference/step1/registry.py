"""Command registry."""


COMMANDS = {}


def register(name, fn):
    COMMANDS[name] = fn


class UnknownCommand(Exception):
    pass


def dispatch(name, arg):
    if name not in COMMANDS:
        raise UnknownCommand(name)
    return COMMANDS[name](arg)


def names():
    return sorted(COMMANDS)
