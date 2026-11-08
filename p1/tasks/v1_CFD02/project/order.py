from rates import fee


def cost(qty):
    return fee(qty) + 1
