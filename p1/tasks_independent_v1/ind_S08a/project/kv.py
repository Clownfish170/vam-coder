"""Key-value text."""


def format_pair(k, v):
    return f"{k}={v}"


def parse_pair(s):
    return s.split("=", 1)
