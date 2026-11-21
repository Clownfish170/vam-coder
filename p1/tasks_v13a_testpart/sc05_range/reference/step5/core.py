def alpha(a):
    if a < 0:
        return 0
    return a + 10


def beta(b):
    return b * 2


def gamma(g):
    return g * 3


def delta(d):
    return alpha(d) + beta(d)
