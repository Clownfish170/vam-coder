"""Fraction helpers."""


def simplify(a, b):
    if a == 0 and b == 0:
        return (0, 1)
    g = _gcd(abs(a), abs(b))
    na, nb = a // g, b // g
    if nb < 0:
        na, nb = -na, -nb
    return (na, nb)


def _gcd(x, y):
    while y:
        x, y = y, x % y
    return x or 1
