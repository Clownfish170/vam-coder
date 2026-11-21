"""Command registry."""


COMMANDS = {}


def register(name, fn):
    COMMANDS[name] = fn


def dispatch(name, arg):
    if name not in COMMANDS:
        raise KeyError(name)
    return COMMANDS[name](arg)


def names():
    return sorted(COMMANDS)
