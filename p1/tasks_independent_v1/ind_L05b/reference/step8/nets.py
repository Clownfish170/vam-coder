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
    seen = {u}
    stack = [u]
    while stack:
        cur = stack.pop()
        for (a, b) in LINKS:
            if a == cur and b not in seen:
                seen.add(b)
                stack.append(b)
    return sorted(seen)


def capped(u, v):
    w = weight(u, v)
    if w is None:
        return None
    return min(w, CAP)
