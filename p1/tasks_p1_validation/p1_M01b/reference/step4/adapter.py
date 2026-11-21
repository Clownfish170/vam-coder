"""Adapter extras"""
from impl import render


def wrap_one(x):
    return [x]


def render_via(data):
    return render(data, "-")
