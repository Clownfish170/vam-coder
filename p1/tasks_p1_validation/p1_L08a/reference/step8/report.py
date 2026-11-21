"""Tax report"""
from hub import compute
from hub import cap_tax


def tax_line(fee):
    return f"fee: {fee}"


def tax_run(qty):
    return tax_line(compute(qty))


def tax_all(fees):
    return [tax_line(cap_tax(f)) for f in fees]
