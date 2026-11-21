"""Keyed depot."""


ROWS = {}


def put(key, rec):
    ROWS[key] = rec


def get(key, default=None):
    return ROWS.get(key, default)
