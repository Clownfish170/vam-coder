"""Text helpers."""


def wrap(s, n):
    return s[:n]


def slugify(s):
    return s.lower().replace(" ", "-")
