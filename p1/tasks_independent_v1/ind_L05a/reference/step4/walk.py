"""Walk helpers."""
from mesh import ADJ


def tag():
    return "walk"


def degree_line(name):
    return f"{name}={len(ADJ.get(name, []))}"
