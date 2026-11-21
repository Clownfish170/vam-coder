"""Reporting helpers."""


def summarize(rows):
    out = {}
    for r in rows:
        out.setdefault(r["group"], []).append(r["value"])
    return out


def groups(rows):
    return sorted({r["group"] for r in rows})
