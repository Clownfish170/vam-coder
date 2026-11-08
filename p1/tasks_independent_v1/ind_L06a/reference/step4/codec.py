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
    return "v2|" + kind + "|" + body + "|" + tag


def decode2(text):
    parts = text.split("|")
    if len(parts) != 4 or parts[0] != "v2":
        raise ValueError("frame2")
    return (parts[1], parts[2], parts[3])


def decode_any(text):
    if text.startswith("v2|"):
        return decode2(text)
    return decode(text)
