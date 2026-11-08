"""Glue extras"""
from impl import glue


def wrap_glue(x):
    return [x]


def glue_via(data):
    return glue(data, "-")
