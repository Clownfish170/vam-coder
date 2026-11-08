"""Export helpers."""

from loader import load


def names():
    return [r["full_name"] for r in load()]


def ages():
    return [r["age"] for r in load()]
