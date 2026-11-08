"""Output sinks."""
from pipeline import run


def join(items, sep=";"):
    return sep.join(items)


def emit(items):
    return join([run(i) for i in items])
