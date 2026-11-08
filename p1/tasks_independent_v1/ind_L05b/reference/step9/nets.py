"""Edge-centric net."""


NODES = set()


LINKS = {}
CAP = 6


def add_node(n):
    NODES.add(n)


def link(u, v, w=1):
    if u == v:
        raise ValueError("self loop")
    LINKS[(u, v)] = w


def nodes():
    return sorted(NODES)


def weight(u, v):
    return LINKS.get((u, v))


def reachable(u):
    seen = {u: 0}
    frontier = [u]
    hops = 0
    while frontier and hops < 2:
        nxt = []
        for cur in frontier:
            for (a, b) in LINKS:
                if a == cur and b not in seen:
                    seen[b] = hops + 1
                    nxt.append(b)
        frontier = nxt
        hops += 1
    return sorted(seen)


def capped(u, v):
    w = weight(u, v)
    if w is None:
        return None
    return min(w, CAP)
