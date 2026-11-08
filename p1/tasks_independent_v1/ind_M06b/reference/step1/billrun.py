"""Bill expression runner."""


def scan(s):
    out = []
    for c in s:
        if c in "+-*/":
            out.append(c)
        elif not c.isspace():
            out.append(c)
    return out


def run(s):
    for t in scan(s):
        if t.isdigit():
            return int(t)
    return 0
