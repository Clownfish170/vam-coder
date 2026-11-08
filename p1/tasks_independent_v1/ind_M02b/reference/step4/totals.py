"""Totals."""

from catalog import load


def sum_prices():
    data = load()
    return sum(r["price"] for r in data.values())


def count_items():
    return len(load())
