"""Basic stats."""


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        raise ValueError("median of empty list")
    if n % 2 == 1:
        return xs[n // 2]
    return (xs[n // 2 - 1] + xs[n // 2]) / 2


def mean(xs):
    return sum(xs) / len(xs) if xs else None
