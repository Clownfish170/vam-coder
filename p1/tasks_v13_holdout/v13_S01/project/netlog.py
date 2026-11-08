"""Tiny network log helpers."""
from backoff import delay


def stamp(msg):
    return "[net] " + msg


def retry_stamp(base, attempt):
    return stamp(str(delay(base, attempt)))
