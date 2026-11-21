"""Public api"""
from impl import render


def call(data, sep=None):
    if sep is None:
        return render(data)
    return render(data, sep)
