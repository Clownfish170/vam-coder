"""Batch factor math"""
from factors import FACTOR


def apply_factor(v):
    return v * FACTOR


def positive(v):
    return v > 0


def factor_pair(a, b):
    return apply_factor(a) + apply_factor(b)
