from ratemap import apply_tier


def quote(x):
    return apply_tier(x, 'gold')


def quote_fast(x):
    return x * 9
