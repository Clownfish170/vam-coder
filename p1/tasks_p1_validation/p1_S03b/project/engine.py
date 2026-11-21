"""Weighted totals"""
from weights import WEIGHT


def apply_weight(v):
    return v + WEIGHT


def positive(v):
    return v > 0
