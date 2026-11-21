"""Pipe codec."""


def encode(kind, body):
    return kind + "|" + body


def decode(text):
    if "|" not in text:
        raise ValueError("frame")
    kind, body = text.split("|", 1)
    if kind.startswith("v") and len(kind) > 1 and kind[1:].isdigit():
        raise ValueError("version")
    return (kind, body)


def encode2(kind, body, tag):
    return "v2|" + kind + "|" + tag + "|" + body


def decode2(text):
    parts = text.split("|")
    if len(parts) != 4 or parts[0] != "v2":
        raise ValueError("frame2")
    return (parts[1], parts[3], parts[2])


def decode_any(text):
    if text.startswith("v2|"):
        return decode2(text)
    return decode(text)


def version_of(text):
    if text.startswith("v2|"):
        return 2
    if "|" in text:
        return 1
    raise ValueError("frame")


def negotiate(theirs):
    common = [v for v in theirs if v in (1, 2)]
    if not common:
        return 1
    return max(common)
