"""Ticket lines"""
from hub import cost


def entry(fee):
    return f"fee: {fee}"


def entry_of(qty):
    return entry(cost(qty))
