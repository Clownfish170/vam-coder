"""Glue facade"""
from impl import glue


def glue_call(data, sep=None):
    if sep is None:
        return glue(data)
    return glue(data, sep)
