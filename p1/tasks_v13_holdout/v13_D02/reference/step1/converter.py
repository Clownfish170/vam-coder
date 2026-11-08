"""Conversion entry points."""
from parserx import normalize


def convert(line):
    return normalize(line).upper()
