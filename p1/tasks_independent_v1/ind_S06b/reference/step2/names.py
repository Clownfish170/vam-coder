"""Slug helpers."""


def slugify(s):
    parts = s.lower().split()
    return "-".join(p for p in parts if p)


def drop_digits(s):
    return "".join(c for c in s if not c.isdigit())
