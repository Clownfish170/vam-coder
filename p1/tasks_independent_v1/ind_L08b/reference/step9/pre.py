"""Before hooks."""


BEFORE = []


def on_before(fn):
    BEFORE.append(fn)
