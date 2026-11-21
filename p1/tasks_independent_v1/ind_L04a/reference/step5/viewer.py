"""Viewer."""
from doc import LINES


def title():
    return "doc-view"


def last_line():
    if not LINES:
        return None
    return LINES[-1]
