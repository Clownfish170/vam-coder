"""Margin report"""
from hub import scale


def row(fee):
    return f"fee: {fee}"


def emit(qty):
    return row(scale(qty))
