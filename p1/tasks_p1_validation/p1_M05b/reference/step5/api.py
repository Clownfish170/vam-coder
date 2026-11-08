"""Stream api"""
from impl import print_stream


def push(data, sep=None):
    if sep is None:
        return print_stream(data)
    return print_stream(data, sep)
