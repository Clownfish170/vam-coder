from pricing import price


def total(qty):
    return price(qty)


def fast_price(qty):
    return qty * 12
