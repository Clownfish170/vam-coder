"""Route registry."""


ROUTES = {}


ORDER = []


def bind(path, handler):
    if path not in ROUTES:
        ORDER.append(path)
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
    return list(ORDER)
