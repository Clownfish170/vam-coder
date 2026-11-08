"""Ingestion."""
from verify import check


def load(rows):
    return [r for r in rows if check(r)]


def keys(rows):
    return [r["id"] for r in rows]
