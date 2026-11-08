"""Side adapters"""
from impl import emit


def wrap_one(x):
    return [x]


def emit_via(data):
    return emit(data, "-")
