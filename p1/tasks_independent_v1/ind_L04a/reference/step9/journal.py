"""Command journal."""


JOURNAL = []


def record(entry):
    JOURNAL.append(entry)


def size():
    return len(JOURNAL)


def history(kind=None):
    if kind is None:
        return list(JOURNAL)
    return [e for e in JOURNAL if e[0] == kind]


def compact():
    if not JOURNAL:
        return None
    keep = JOURNAL[-3:]
    JOURNAL[:] = keep
    return keep[-1]
