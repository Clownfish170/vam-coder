from thresholds import CUT, MAX_N


def keep(x):
    return x >= CUT and x <= MAX_N


def count(xs):
    return sum(1 for x in xs if keep(x))
