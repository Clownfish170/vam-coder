from thresholds import CUT


def keep(x):
    return x > CUT


def count(xs):
    if not xs:
        return 0
    return sum(1 for x in xs if keep(x))
