"""Padding."""


def pad_left(s, n, ch):
    if len(s) >= n:
        return s
    return ch * (n - len(s)) + s


def pad_right(s, n, ch):
    if len(s) >= n:
        return s
    return s + ch * (n - len(s))
