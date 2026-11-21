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
    out = ROUTES[path](payload)
    if out is None:
        return "ok"
    return out


def paths():
    return sorted(ROUTES)
