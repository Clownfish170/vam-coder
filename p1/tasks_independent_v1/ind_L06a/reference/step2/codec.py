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
