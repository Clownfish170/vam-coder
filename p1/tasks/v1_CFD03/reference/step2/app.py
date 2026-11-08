from util import clamp


def norm(x):
    return clamp(x, 0, 10)


def batch(vals):
    return [norm(v) for v in vals]
