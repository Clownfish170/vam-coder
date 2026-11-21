def helper(x):
    return x * 2


def helper_sum(xs):
    return sum(helper(x) for x in xs)


def helper_avg(xs):
    return helper_sum(xs) / max(1, len(xs))


def helper_max(xs):
    return max(xs) if xs else 0
