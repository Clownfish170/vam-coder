"""Key-value text."""


def format_pair(k, v):
    return f"{k}={v}"


def parse_pair(s):
    if "=" not in s:
        raise ValueError("missing =")
    k, v = s.split("=", 1)
    return (k, v)
