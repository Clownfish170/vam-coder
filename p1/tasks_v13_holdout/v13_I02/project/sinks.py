"""Output sinks."""


def join(items, sep=";"):
    return sep.join(items)


def emit(items):
    return join(items)
