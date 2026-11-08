"""Entry facade"""
from impl import write_row


def send(data, sep=None):
    if sep is None:
        return write_row(data)
    return write_row(data, sep)
