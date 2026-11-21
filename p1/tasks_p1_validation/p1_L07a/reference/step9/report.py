"""Loan report"""
from hub import interest
from hub import cap_interest


def line_i(fee):
    return f"fee: {fee}"


def line_of(qty):
    return line_i(interest(qty))


def lines_of(fees):
    return [line_i(cap_interest(f)) for f in fees]
