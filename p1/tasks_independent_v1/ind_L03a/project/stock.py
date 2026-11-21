"""Stock records."""


ITEMS = {}


def receive(sku, qty):
    ITEMS[sku] = ITEMS.get(sku, 0) + qty
