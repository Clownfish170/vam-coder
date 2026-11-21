"""Companion module (target)."""


def pick_route(nodes):
    return sorted(nodes)[-1] if nodes else None


def summarize(nodes):
    return len(nodes)
