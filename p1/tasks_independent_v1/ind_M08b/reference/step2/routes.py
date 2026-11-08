"""Route registry."""


ROUTES = {}


def bind(path, handler):
    ROUTES[path] = handler


class UnknownRoute(Exception):
    pass


ALIASES = {}


def bind_alias(alias, path):
    ALIASES[alias] = path


def serve(path, payload):
    path = ALIASES.get(path, path)
    if path not in ROUTES:
        raise UnknownRoute(path)
    return ROUTES[path](payload)


def paths():
    return sorted(ROUTES)
