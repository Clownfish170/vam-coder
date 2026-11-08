"""Priority panel."""


PLUGINS = []


def plug(name, fn):
    PLUGINS.append((name, fn))


def count():
    return len(PLUGINS)
