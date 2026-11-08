"""Mid frames"""
from leaf import render_n


def gate(n):
    return render_n(n) + 1


def gate_x2(n):
    return render_n(n) * 2
