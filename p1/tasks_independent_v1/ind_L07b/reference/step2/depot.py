"""Keyed depot."""


ROWS = {}


def put(key, rec):
    if key == "":
        raise ValueError("key")
    ROWS[key] = rec


def get(key, default=None):
    return ROWS.get(key, default)
