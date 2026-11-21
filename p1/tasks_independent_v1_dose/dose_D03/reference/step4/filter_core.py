from thresholds import CUT


def keep(x):
    return x >= CUT


def count(xs):
    return sum(1 for x in xs if keep(x))
