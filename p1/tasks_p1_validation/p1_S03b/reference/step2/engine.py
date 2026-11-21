"""Weighted totals"""
from weights import WEIGHT


def apply_weight(v):
    return v * WEIGHT


def positive(v):
    return v > 0


def weight_pair(a, b):
    return apply_weight(a) + apply_weight(b)
