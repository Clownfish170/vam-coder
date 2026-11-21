from pool_cap import CAP


def acquire():
    return CAP - 1


def remaining(used):
    if used < 0:
        return CAP
    if used > CAP:
        return 0
    return CAP - used
