"""Fraction helpers."""


def simplify(a, b):
    if b == 0:
        raise ValueError("b is zero")
    g = _gcd(abs(a), abs(b))
    na, nb = a // g, b // g
    if nb < 0:
        na, nb = -na, -nb
    return (na, nb)


def _gcd(x, y):
    while y:
        x, y = y, x % y
    return x or 1
