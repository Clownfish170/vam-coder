"""Render pipeline"""


def render(data, sep=", "):
    return sep.join(str(x) for x in data)
