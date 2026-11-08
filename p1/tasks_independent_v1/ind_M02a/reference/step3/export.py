"""Export helpers."""

from loader import load


def names():
    return [r["name"] for r in load()]


def ages():
    return [r["age"] for r in load()]
