"""Plugin registry."""
import hooks


HANDLERS = {}
ALIASES = {}


def register(name, fn):
    if name in HANDLERS:
        raise ValueError("name")
    HANDLERS[name] = fn


def alias(old, new):
    if new not in HANDLERS and new not in ALIASES:
        raise KeyError(new)
    ALIASES[old] = new


def names():
    return list(HANDLERS)


def dispatch(name, *args):
    seen = 0
    while name in ALIASES:
        name = ALIASES[name]
        seen += 1
        if seen > 10:
            raise ValueError("alias loop")
    fn = HANDLERS[name]
    result = fn(*args)
    for hook in hooks.AFTER:
        hook(name, result)
    return result
