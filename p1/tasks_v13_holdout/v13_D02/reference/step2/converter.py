"""Conversion entry points."""
from parserx import normalize


def convert(line):
    return normalize(line).upper()


def bulk(lines):
    if not lines:
        return ""
    return "|".join(convert(ln) for ln in lines)
