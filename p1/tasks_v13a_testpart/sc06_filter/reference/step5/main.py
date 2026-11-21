from limits import MAX


def clamp(n):
    if n < 0:
        return 0
    return min(n, MAX)


def zero(n):
    if n == 0:
        return -1
    return 0 if n < 0 else n


def bounded(n):
    return zero(clamp(n))
