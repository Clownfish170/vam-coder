"""Shipping notes."""
import stock


def note(sku):
    return f"sku={sku}"


def reservation_line(sku, qty):
    if stock.reserve(sku, qty):
        return f"held={sku}"
    return f"short={sku}"
