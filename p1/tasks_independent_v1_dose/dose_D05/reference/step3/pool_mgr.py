from pool_cap import CAP


def acquire():
    return CAP - 1


def remaining(used):
    return CAP - used
