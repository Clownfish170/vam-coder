"""Audit trail."""

EVENTS = []


def record(name):
    EVENTS.append(name)
    return len(EVENTS)


def last():
    return EVENTS[-1] if EVENTS else None
