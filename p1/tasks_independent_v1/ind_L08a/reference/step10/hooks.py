"""Hook bus."""


AFTER = []


def on_after(fn):
    AFTER.append(fn)


def clear():
    n = len(AFTER)
    AFTER.clear()
    return n
