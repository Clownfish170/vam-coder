"""Route registry."""


ROUTES = {}


def bind(path, handler):
    ROUTES[path] = handler


def serve(path, payload):
    if path not in ROUTES:
        raise KeyError(path)
    return ROUTES[path](payload)


def paths():
    return sorted(ROUTES)
