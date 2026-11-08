"""Outer layer"""
from impl import join_items


def run_join(data, sep=None):
    if sep is None:
        return join_items(data)
    return join_items(data, sep)
