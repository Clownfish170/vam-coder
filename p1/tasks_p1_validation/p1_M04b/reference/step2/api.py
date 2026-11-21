"""Entry facade"""
from impl import write_row


def send(data):
    return write_row(data)
