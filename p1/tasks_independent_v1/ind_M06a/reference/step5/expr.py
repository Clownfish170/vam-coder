"""Expression parser."""


def tokenize(s):
    out = []
    buf = ""
    for ch in s:
        if ch in "+-*/":
            if buf:
                out.append(buf)
                buf = ""
            out.append(ch)
        elif ch.isspace():
            if buf:
                out.append(buf)
                buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def evaluate(s):
    toks = tokenize(s)
    total = int(toks[0])
    i = 1
    while i < len(toks):
        if toks[i] == "+":
            total = total + int(toks[i + 1])
        elif toks[i] == "-":
            total = total - int(toks[i + 1])
        elif toks[i] == "*":
            total = total * int(toks[i + 1])
        i += 2
    return total
