"""Ingestion."""
from verify import check


def load(rows):
    return list(rows)


def keys(rows):
    return [r["id"] for r in rows]
