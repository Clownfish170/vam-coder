"""Priority panel."""
import pre


PLUGINS = []
ALIASES = {}


def plug(name, fn):
    if any(p[0] == name for p in PLUGINS):
        raise ValueError("name")
    PLUGINS.append((name, fn))


def alias(old, new):
    if new not in {p[0] for p in PLUGINS}:
        raise KeyError(new)
    ALIASES[old] = new


def count():
    return len(PLUGINS)


def run(name, *args):
    name = ALIASES.get(name, name)
    for hook in pre.BEFORE:
        hook(name)
    for pname, fn in PLUGINS:
        if pname == name:
            return fn(*args)
    raise KeyError(name)
