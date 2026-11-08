"""Grade report"""
from hub import points
from hub import cap_pts


def label(fee):
    return f"fee: {fee}"


def label_for(qty):
    return label(points(qty))


def labels(fees):
    return [label(cap_pts(f)) for f in fees]
