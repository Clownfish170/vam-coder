"""Fee report"""
from hub import quote


def line(fee):
    return f"fee: {fee}"


def run(qty):
    return line(quote(qty))
