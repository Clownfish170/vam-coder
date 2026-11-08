"""Formatting helpers."""


def pad(s, n):
    return s.rjust(n)


def wrap(s, width):
    return [s[i:i + width] for i in range(0, len(s), width)]
