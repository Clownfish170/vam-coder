"""Registry of engines."""

REGISTRY = {"default": "engine"}


def register(name):
    REGISTRY[name] = True
    return name
