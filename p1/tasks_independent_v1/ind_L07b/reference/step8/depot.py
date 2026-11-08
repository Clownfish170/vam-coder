"""Keyed depot."""
import quota


ROWS = {}


def put(key, rec):
    if key == "":
        raise ValueError("key")
    if "name" not in rec:
        raise ValueError("name")
    ROWS[key] = rec


def get(key, default=None):
    return ROWS.get(key, default)


def where(field, value):
    out = []
    for key in sorted(ROWS):
        rec = ROWS[key]
        if rec.get(field) == value:
            out.append(rec)
    return out


def page(offset):
    start = offset * quota.PAGE_SIZE
    keys = sorted(ROWS)[start:start + quota.PAGE_SIZE]
    return [ROWS[k] for k in keys]


def top(field, n):
    ordered = sorted(ROWS, key=lambda k: (-ROWS[k][field], k))
    return [ROWS[k] for k in ordered[:n]]
