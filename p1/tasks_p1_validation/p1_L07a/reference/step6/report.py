"""Loan report"""
from hub import interest


def line_i(fee):
    return f"fee: {fee}"


def line_of(qty):
    return line_i(interest(qty))
