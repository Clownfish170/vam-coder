"""Geometry helpers."""
from units import MARGIN


def area(w, h):
    return w * h


def border_area(w, h):
    return (w + MARGIN) * (h + MARGIN)


def padded_area(w, h):
    return w * h * (1 + MARGIN)
