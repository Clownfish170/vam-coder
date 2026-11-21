"""Walk helpers."""
from mesh import ADJ


def tag():
    return "walk"


def degree_line(name):
    return f"{name}={len(ADJ.get(name, []))}"


def dfs(start):
    seen = []
    stack = [start]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.append(cur)
        for nb in reversed(ADJ.get(cur, [])):
            stack.append(nb)
    return seen
