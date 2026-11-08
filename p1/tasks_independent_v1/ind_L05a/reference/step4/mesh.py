"""Mesh graph."""
import costs


NODES = []


ADJ = {}


def add_node(name):
    if name not in NODES:
        NODES.append(name)


def add_edge(a, b):
    if b in ADJ.get(a, []):
        return False
    ADJ.setdefault(a, []).append(b)
    ADJ.setdefault(b, []).append(a)
    return True


def has_node(name):
    return name in NODES


def weight(a, b):
    if b not in ADJ.get(a, []):
        return None
    return costs.EDGE_W.get((a, b), 1)
