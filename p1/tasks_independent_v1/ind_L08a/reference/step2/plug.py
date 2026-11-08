"""Plugin registry."""


HANDLERS = {}


def register(name, fn):
    HANDLERS[name] = fn


def names():
    return list(HANDLERS)


def dispatch(name, *args):
    fn = HANDLERS[name]
    return fn(*args)
