"""View helpers."""
import shelf


def heading():
    return "shelf"


def top_names(n):
    ordered = sorted(shelf.RECORDS, key=lambda r: (-r["score"], r["name"]))
    return [r["name"] for r in ordered[:n]]
