"""Grade report"""
from hub import points


def label(fee):
    return f"fee: {fee}"


def label_for(qty):
    return label(points(qty))
