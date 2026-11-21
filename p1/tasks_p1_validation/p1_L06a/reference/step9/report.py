"""Rent report"""
from hub import fee_of
from hub import cap_rent


def desc(fee):
    return f"fee: {fee}"


def desc_of(qty):
    return desc(fee_of(qty))


def descs(fees):
    return [desc(cap_rent(f)) for f in fees]
