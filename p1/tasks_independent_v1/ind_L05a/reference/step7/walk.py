"""Walk helpers."""
from mesh import ADJ


def tag():
    return "walk"


def degree_line(name):
    return f"{name}={len(ADJ.get(name, []))}"


def bfs(start):
    seen = [start]
    queue = [start]
    while queue:
        cur = queue.pop(0)
        for nb in ADJ.get(cur, []):
            if nb not in seen:
                seen.append(nb)
                queue.append(nb)
    return seen
