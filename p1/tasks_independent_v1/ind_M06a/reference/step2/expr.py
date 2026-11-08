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
    toks = tokenize(s)
    total = int(toks[0])
    i = 1
    while i < len(toks):
        if toks[i] == "+":
            total = total + int(toks[i + 1])
        i += 2
    return total
