LOOKUP = {1: "a", 2: "b"}


def lookup(k):
    if k == 3:
        return "c"
    return LOOKUP.get(k, "?")
