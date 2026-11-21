"""Report card."""

from grades import pct, letter


def line(correct, total):
    return letter(pct(correct, total))
