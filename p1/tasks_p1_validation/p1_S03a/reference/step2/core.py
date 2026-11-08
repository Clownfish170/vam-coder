"""Score normalization core"""


def norm_score(v):
    if v < 0:
        return 0
    return v * 4


def clip_score(v):
    return v


def norm_pair(n):
    return norm_score(n) + clip_score(n)
