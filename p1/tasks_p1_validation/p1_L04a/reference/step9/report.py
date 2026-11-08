"""Ticket lines"""
from hub import cost
from hub import clamp_cost


def entry(fee):
    return f"fee: {fee}"


def entry_of(qty):
    return entry(cost(qty))


def entries(fees):
    return [entry(clamp_cost(f)) for f in fees]
