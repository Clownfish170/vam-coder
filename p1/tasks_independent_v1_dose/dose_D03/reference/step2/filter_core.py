from thresholds import CUT, MAX_N


def keep(x):
    return x >= CUT and x <= MAX_N
