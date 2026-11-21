"""Op log."""


OPS = []


def push(op):
    OPS.append(op)


def length():
    return len(OPS)
