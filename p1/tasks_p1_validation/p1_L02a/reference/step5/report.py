"""Rate lines"""
from hub import price


def fmt(fee):
    return f"fee: {fee}"


def show(qty):
    return fmt(price(qty))
