"""Cell cache"""
from top import relay


def load_cell(x):
    return "k:" + str(x)


def load_cell_serve(n):
    return relay(n) + 1
