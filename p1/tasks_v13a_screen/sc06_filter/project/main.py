from limits import MAX


def clamp(n):
    return min(n, MAX)


def zero(n):
    return 0 if n < 0 else n
