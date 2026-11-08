"""Cell extras"""
from impl import join_cells


def wrap_cell(x):
    return [x]


def cells_via(data):
    return join_cells(data, "-")
