"""Catalog rows."""
from caps import MAX_HOLD


ROWS = []


def add_row(sku, qty):
    if find(sku) is not None:
        raise ValueError("sku")
    ROWS.append({"sku": sku, "qty": qty})


def find(sku):
    for row in ROWS:
        if row["sku"] == sku:
            return row
    return None


def set_qty(sku, qty):
    row = find(sku)
    if row is None:
        return False
    row["qty"] = qty
    return True


def total():
    return sum(row["qty"] for row in ROWS)


def hold(sku, n):
    if n <= 0:
        raise ValueError("n")
    if n > MAX_HOLD:
        raise ValueError("n")
    row = find(sku)
    if row is None:
        raise KeyError(sku)
    row["qty"] = row["qty"] - n
    return row["qty"]


def low_rows(k):
    return sorted(row["sku"] for row in ROWS if row["qty"] < k)
