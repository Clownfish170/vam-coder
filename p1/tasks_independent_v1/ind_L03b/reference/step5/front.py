"""Front desk."""
from catalog import find


def greeting():
    return "welcome"


def stock_line(sku):
    row = find(sku)
    if row is None:
        return f"sku={sku} qty=missing"
    return f"sku={sku} qty={row['qty']}"
