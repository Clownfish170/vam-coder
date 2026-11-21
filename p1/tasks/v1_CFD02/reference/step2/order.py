from rates import fee


def cost(qty):
    return fee(qty) + 1


def cost_fast(qty):
    return qty * 5 + 1
