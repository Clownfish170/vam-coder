"""Mesh graph."""


NODES = []


ADJ = {}


def add_node(name):
    if name not in NODES:
        NODES.append(name)


def add_edge(a, b):
    ADJ.setdefault(a, []).append(b)
    ADJ.setdefault(b, []).append(a)


def has_node(name):
    return name in NODES
