"""Extra layer"""
from impl import join_items


def wrap_item(x):
    return [x]


def join_via(data):
    return join_items(data, "-")
