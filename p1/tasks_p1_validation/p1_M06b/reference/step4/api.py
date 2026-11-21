"""Cell api"""
from impl import join_cells


def open_cells(data, sep=None):
    if sep is None:
        return join_cells(data)
    return join_cells(data, sep)
