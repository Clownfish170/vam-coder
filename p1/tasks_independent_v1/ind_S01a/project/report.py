"""Reporting helpers."""


from stats import mean


def average_line(xs):
    return f"avg={mean(xs)}"
