from pool_cap import CAP


def acquire():
    return CAP - 1


def remaining(used):
    if used < 0:
        return CAP
    return CAP - used
