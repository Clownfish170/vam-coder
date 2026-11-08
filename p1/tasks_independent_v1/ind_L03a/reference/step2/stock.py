"""Stock records."""


ITEMS = {}


def receive(sku, qty):
    if qty <= 0:
        raise ValueError("qty")
    ITEMS[sku] = ITEMS.get(sku, 0) + qty


def available(sku):
    return ITEMS.get(sku, 0)
