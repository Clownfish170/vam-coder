"""Token/text counting utilities."""


def parse_n(s):
    if s.strip() == "":
        return 0
    v = int(s)
    if v < 0:
        return 0
    return v


def band(n):
    if n > 100:
        return "high"
    return "mid"
