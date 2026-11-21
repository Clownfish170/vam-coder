"""Plugin registry."""


HANDLERS = {}
ALIASES = {}


def register(name, fn):
    if name in HANDLERS:
        raise ValueError("name")
    HANDLERS[name] = fn


def alias(old, new):
    if new not in HANDLERS:
        raise KeyError(new)
    ALIASES[old] = new


def names():
    return list(HANDLERS)


def dispatch(name, *args):
    if name in ALIASES:
        name = ALIASES[name]
    fn = HANDLERS[name]
    return fn(*args)
