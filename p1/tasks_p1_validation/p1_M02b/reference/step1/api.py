"""Service facade"""
from impl import emit


def invoke(data):
    return emit(data)
