"""Catalog rows."""


ROWS = []


def add_row(sku, qty):
    ROWS.append({"sku": sku, "qty": qty})


def find(sku):
    for row in ROWS:
        if row["sku"] == sku:
            return row
    return None
