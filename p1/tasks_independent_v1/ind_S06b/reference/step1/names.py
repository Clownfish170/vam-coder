"""Slug helpers."""


def slugify(s):
    parts = s.lower().split()
    return "-".join(p for p in parts if p)
