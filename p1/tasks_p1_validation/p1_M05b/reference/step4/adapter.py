"""Stream extras"""
from impl import print_stream


def wrap_push(x):
    return [x]


def print_via(data):
    return print_stream(data, "-")
