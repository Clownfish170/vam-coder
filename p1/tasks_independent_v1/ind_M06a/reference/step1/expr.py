"""Expression parser."""


def tokenize(s):
    out = []
    for ch in s:
        if ch in "+-*/":
            out.append(ch)
        elif not ch.isspace():
            out.append(ch)
    return out


def evaluate(s):
    for t in tokenize(s):
        if t.isdigit():
            return int(t)
    return 0
