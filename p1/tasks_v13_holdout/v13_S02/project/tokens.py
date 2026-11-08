"""Token/text counting utilities."""


def parse_n(s):
    return int(s)


def band(n):
    if n > 100:
        return "high"
    return "mid"
