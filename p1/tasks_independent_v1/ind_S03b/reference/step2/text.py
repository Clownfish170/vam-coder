"""Text helpers."""


def wrap(s, n):
    return s[:n]


def slugify(s):
    return s.lower().replace(" ", "-")


def slug_list(items):
    return [slugify(x) for x in items]
