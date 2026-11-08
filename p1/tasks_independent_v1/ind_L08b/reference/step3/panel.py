"""Priority panel."""


PLUGINS = []


def plug(name, fn):
    if any(p[0] == name for p in PLUGINS):
        raise ValueError("name")
    PLUGINS.append((name, fn))


def count():
    return len(PLUGINS)


def run(name, *args):
    for pname, fn in PLUGINS:
        if pname == name:
            return fn(*args)
    raise KeyError(name)
