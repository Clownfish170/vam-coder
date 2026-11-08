from tax import tax_rate


def grand_total(cents):
    return int(cents * (1 + tax_rate()))


def net_total(cents):
    return int(cents / (1 + tax_rate()))
