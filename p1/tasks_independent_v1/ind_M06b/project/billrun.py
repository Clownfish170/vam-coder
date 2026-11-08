"""Bill expression runner."""


def scan(s):
    return s.split()


def run(s):
    for t in scan(s):
        if t.isdigit():
            return int(t)
    return 0
