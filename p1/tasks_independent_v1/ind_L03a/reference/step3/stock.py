"""Stock records."""


ITEMS = {}


def receive(sku, qty):
    if qty <= 0:
        raise ValueError("qty")
    ITEMS[sku] = ITEMS.get(sku, 0) + qty


def available(sku):
    return ITEMS.get(sku, 0)


def reserve(sku, qty):
    have = ITEMS.get(sku, 0)
    if have < qty:
        return False
    ITEMS[sku] = have - qty
    return True
