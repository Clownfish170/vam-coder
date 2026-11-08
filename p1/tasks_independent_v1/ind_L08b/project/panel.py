"""Priority panel."""


PLUGINS = []


def plug(name, fn):
    PLUGINS.append((name, fn))
