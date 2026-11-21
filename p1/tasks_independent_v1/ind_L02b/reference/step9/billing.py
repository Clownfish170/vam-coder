"""Billing summary."""
from meter import day_charge, USAGE


def header():
    return "bill"


def charge_line(day):
    return f"day={day} charge={day_charge(day)}"


def total_charge():
    return sum(day_charge(d) for d in USAGE)
