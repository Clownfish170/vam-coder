from store import put


def seed():
    d = {}
    put(d, 'a', 1)
    return d
