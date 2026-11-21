"""Tax report"""
from hub import compute


def tax_line(fee):
    return f"fee: {fee}"


def tax_run(qty):
    return tax_line(compute(qty))
