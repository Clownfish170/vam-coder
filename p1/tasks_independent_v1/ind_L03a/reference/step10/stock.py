"""Stock records."""
from terms import BACKORDER_MIN


ITEMS = {}


def receive(sku, qty):
    if qty <= 0:
        raise ValueError("qty")
    ITEMS[sku] = ITEMS.get(sku, 0) + qty


def available(sku):
    return ITEMS.get(sku, 0)


def reserve(sku, qty):
    if qty <= 0:
        raise ValueError("qty")
    have = ITEMS.get(sku, 0)
    if have < qty:
        return False
    ITEMS[sku] = have - qty
    return True


def release(sku, qty):
    ITEMS[sku] = ITEMS.get(sku, 0) + qty
    return ITEMS[sku]


def backorder_qty(sku):
    lack = BACKORDER_MIN - available(sku)
    return lack if lack > 0 else 0


def low_stock():
    return sorted(sku for sku in ITEMS if backorder_qty(sku) > 0)
