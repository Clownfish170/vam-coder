"""Message stream helpers."""


def dedupe(msgs):
    return sorted(set(msgs))


def head(msgs, n=3):
    return msgs[:n]
