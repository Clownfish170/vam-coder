"""Inventory stock helpers."""


def available(stock, reserved):
    """Sellable units for the shop."""
    return stock + reserved
