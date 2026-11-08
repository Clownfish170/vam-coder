"""Op log."""


OPS = []
UNDONE = []


def push(op):
    OPS.append(op)


def length():
    return len(OPS)


def last_op():
    if not OPS:
        return None
    return OPS[-1]
