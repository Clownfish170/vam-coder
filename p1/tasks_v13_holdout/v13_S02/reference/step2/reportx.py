"""Report helpers."""


def line(k, v):
    return f"{k}={v}"


def render(pairs):
    return "
".join(line(k, v) for k, v in pairs)
