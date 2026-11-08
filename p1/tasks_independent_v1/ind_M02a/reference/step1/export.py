"""Export helpers."""

from loader import load


def names():
    return [r["name"] for r in load()]
