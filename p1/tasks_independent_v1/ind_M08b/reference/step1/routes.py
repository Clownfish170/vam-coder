"""Route registry."""


ROUTES = {}


def bind(path, handler):
    ROUTES[path] = handler


class UnknownRoute(Exception):
    pass


def serve(path, payload):
    if path not in ROUTES:
        raise UnknownRoute(path)
    return ROUTES[path](payload)


def paths():
    return sorted(ROUTES)
