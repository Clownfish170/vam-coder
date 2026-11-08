"""Margin report"""
from hub import scale
from hub import bound


def row(fee):
    return f"fee: {fee}"


def emit(qty):
    return row(scale(qty))


def emit_all(fees):
    return [row(bound(f)) for f in fees]
