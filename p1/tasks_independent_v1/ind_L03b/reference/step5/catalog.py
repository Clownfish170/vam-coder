"""Catalog rows."""


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
