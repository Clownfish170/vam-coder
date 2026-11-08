"""Service facade"""
from impl import emit


def invoke(data, sep=None):
    if sep is None:
        return emit(data)
    return emit(data, sep)
