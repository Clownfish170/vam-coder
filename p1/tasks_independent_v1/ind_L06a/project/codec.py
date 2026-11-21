"""Pipe codec."""


def encode(kind, body):
    return kind + "|" + body


def decode(text):
    return text.split("|", 1)
