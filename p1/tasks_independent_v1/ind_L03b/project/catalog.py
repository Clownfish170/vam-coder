"""Catalog rows."""


ROWS = []


def add_row(sku, qty):
    ROWS.append({"sku": sku, "qty": qty})
