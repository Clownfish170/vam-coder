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
    toks = scan(s)
    acc = int(toks[0])
    i = 1
    while i < len(toks):
        if toks[i] == "+":
            acc = acc + int(toks[i + 1])
        elif toks[i] == "-":
            acc = acc - int(toks[i + 1])
        i += 2
    return acc
