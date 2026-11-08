"""Mid frames"""
from leaf import render_n


def gate(n, boost):
    return render_n(n) + 1 + boost


def gate_x2(n):
    return render_n(n) * 2
