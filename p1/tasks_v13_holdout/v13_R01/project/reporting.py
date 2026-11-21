"""Reporting helpers."""


def summarize(rows):
    out = {}
    for r in rows:
        out.setdefault(r["group"], set()).add(r["value"])
    return out


def groups(rows):
    return sorted({r["group"] for r in rows})
