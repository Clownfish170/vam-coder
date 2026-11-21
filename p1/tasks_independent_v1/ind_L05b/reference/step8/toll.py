"""Toll helpers."""
import nets


def label(u, v):
    return f"{u}->{v}"


def heaviest():
    if not nets.LINKS:
        return None
    best = max(nets.LINKS.values())
    pairs = [k for k, w in nets.LINKS.items() if w == best]
    return min(pairs)
