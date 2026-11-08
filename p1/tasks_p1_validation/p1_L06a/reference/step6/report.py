"""Rent report"""
from hub import fee_of


def desc(fee):
    return f"fee: {fee}"


def desc_of(qty):
    return desc(fee_of(qty))
