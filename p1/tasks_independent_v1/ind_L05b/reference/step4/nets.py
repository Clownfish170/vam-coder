"""Edge-centric net."""


NODES = set()


LINKS = {}


def add_node(n):
    NODES.add(n)


def link(u, v, w=1):
    if u == v:
        raise ValueError("self loop")
    LINKS[(u, v)] = w
    LINKS[(v, u)] = w


def nodes():
    return sorted(NODES)


def weight(u, v):
    return LINKS.get((u, v))
