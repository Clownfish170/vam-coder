from score_w import W_BASE, W_BONUS


def score(v):
    s = v * W_BASE
    if v > 0:
        s += W_BONUS
    return s


def total(xs):
    return sum(score(v) for v in xs)
