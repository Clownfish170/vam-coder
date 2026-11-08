"""Expression parser."""


def tokenize(s):
    return s.split()


def evaluate(s):
    for t in tokenize(s):
        if t.isdigit():
            return int(t)
    return 0
