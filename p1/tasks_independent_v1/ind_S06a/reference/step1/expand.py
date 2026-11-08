"""Padding."""


def pad_left(s, n, ch):
    if len(s) >= n:
        return s
    return ch * (n - len(s)) + s
