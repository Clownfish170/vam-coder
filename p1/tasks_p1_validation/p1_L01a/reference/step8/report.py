"""Fee report"""
from hub import quote
from hub import cap_fee


def line(fee):
    return f"fee: {fee}"


def run(qty):
    return line(quote(qty))


def summary(fees):
    return [line(cap_fee(f)) for f in fees]
