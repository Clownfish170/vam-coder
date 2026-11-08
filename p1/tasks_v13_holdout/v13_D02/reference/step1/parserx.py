"""Parsing helpers."""
from cleanup import squash


def normalize(s):
    return squash(s).lower()


def fields(line):
    return line.split(",")
