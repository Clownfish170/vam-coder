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
