"""Weight scaling helpers"""


def scale_w(v):
    if v < 0:
        return 0
    return v * 6


def raw_w(v):
    return v


def scale_pair(n):
    return scale_w(n) + raw_w(n)
