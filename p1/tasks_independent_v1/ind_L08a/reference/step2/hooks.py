"""Hook bus."""


AFTER = []


def on_after(fn):
    AFTER.append(fn)
