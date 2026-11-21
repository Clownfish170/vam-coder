"""Bill expression runner."""


def scan(s):
    out = []
    buf = ""
    for c in s:
        if c in "+-*/":
            if buf:
                out.append(buf)
                buf = ""
            out.append(c)
        elif c.isspace():
            if buf:
                out.append(buf)
                buf = ""
        else:
            buf += c
    if buf:
        out.append(buf)
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
        elif toks[i] == "*":
            acc = acc * int(toks[i + 1])
        i += 2
    return acc
