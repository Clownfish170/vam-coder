"""Seq extras"""
from impl import build_seq


def wrap_seq(x):
    return [x]


def seq_via(data):
    return build_seq(data, "-")
