"""Billing summary."""
from meter import day_charge


def header():
    return "bill"


def charge_line(day):
    return f"day={day} charge={day_charge(day)}"
