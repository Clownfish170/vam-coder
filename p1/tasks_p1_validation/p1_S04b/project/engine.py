"""Margin arithmetic"""
from margins import MARGIN_PCT


def apply_margin(v):
    return v + MARGIN_PCT


def positive(v):
    return v > 0
