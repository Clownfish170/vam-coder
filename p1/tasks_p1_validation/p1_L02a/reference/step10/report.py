"""Rate lines"""
from hub import price
from hub import apply_cap


def fmt(fee):
    return f"fee: {fee}"


def show(qty):
    return fmt(price(qty))


def show_many(fees):
    return [fmt(apply_cap(f)) for f in fees]
