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
    ADJ.setdefault(b, [])
    return True


def has_node(name):
    return name in NODES


def weight(a, b):
    if b not in ADJ.get(a, []):
        return None
    return costs.EDGE_W.get((a, b), 1)


def connected(a, b):
    if a == b:
        return True
    seen = {a}
    stack = [a]
    while stack:
        cur = stack.pop()
        for nb in ADJ.get(cur, []):
            if nb == b:
                return True
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False
