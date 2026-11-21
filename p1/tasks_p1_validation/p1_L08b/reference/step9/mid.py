"""Mid frames"""
from leaf import render_n


def gate(n, boost):
    if boost < 0:
        raise ValueError("boost must be >= 0")
    return render_n(n) + 1 + boost


def gate_x2(n):
    return render_n(n) * 2
