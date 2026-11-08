"""Text cleanup helpers."""


def strip_noise(s):
    return "".join(ch for ch in s if ch.isprintable())


def squash(s):
    return " ".join(s.split())
