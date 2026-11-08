"""Entry extras"""
from impl import write_row


def wrap_row(x):
    return [x]


def write_via(data):
    return write_row(data, "-")
