"""Keyed depot."""


ROWS = {}


def put(key, rec):
    ROWS[key] = rec
