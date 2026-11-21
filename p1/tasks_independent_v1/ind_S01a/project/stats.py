"""Basic stats."""


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2]


def mean(xs):
    return sum(xs) / len(xs) if xs else None
