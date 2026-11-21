"""Tiny app."""


from config import load


def describe():
    cfg = load()
    return f"retries={cfg['retries']}"
