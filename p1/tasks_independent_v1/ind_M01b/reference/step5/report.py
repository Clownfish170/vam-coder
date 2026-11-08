"""Report card."""

from grades import pct, letter


def line(correct, total):
    return letter(pct(correct, total))


def average_score(rows):
    if not rows:
        return 0.0
    return sum(pct(c, t) for c, t in rows) / len(rows)
