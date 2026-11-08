"""Message stream helpers."""


def dedupe(msgs):
    out = []
    for m in msgs:
        if m not in out:
            out.append(m)
    return out


def head(msgs, n=3):
    return msgs[:n]
