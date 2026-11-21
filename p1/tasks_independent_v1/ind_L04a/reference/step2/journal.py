"""Command journal."""


JOURNAL = []


def record(entry):
    JOURNAL.append(entry)


def size():
    return len(JOURNAL)
