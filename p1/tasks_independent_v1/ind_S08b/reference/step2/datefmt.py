"""Dates."""


def format_date(y, m, d):
    return f"{y:04d}-{m:02d}-{d:02d}"


def parse_date(s):
    if len(s) != 10 or s[4] != "-" or s[7] != "-":
        raise ValueError("bad format")
    y, m, d = s[:4], s[5:7], s[8:10]
    if not (y.isdigit() and m.isdigit() and d.isdigit()):
        raise ValueError("bad digits")
    return (int(y), int(m), int(d))
