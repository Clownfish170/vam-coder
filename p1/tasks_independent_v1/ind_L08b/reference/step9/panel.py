"""Priority panel."""
import pre


PLUGINS = []
ALIASES = {}
SILENT = False


def plug(name, fn, prio=0):
    if any(p[0] == name for p in PLUGINS):
        raise ValueError("name")
    PLUGINS.append((name, fn, prio))


def alias(old, new):
    if new not in {p[0] for p in PLUGINS}:
        raise KeyError(new)
    ALIASES[old] = new


def count():
    return len(PLUGINS)


def run(name, *args):
    name = ALIASES.get(name, name)
    for hook in pre.BEFORE:
        if hook(name) is False:
            return None
    for pname, fn, _prio in PLUGINS:
        if pname == name:
            return fn(*args)
    if SILENT:
        return None
    raise KeyError(name)


def run_all(*args):
    ordered = sorted(PLUGINS, key=lambda p: -p[2])
    return [fn(*args) for _n, fn, _p in ordered]
