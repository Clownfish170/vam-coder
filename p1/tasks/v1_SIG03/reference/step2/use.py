from store import put


def seed():
    d = {}
    put(d, 'a', 1)
    return d


def seed_b():
    d = {}
    put(d, 'a', 2)
    put(d, 'b', 3)
    return d
