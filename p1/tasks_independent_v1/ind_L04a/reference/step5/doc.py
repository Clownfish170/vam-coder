"""Line document."""
from journal import record


LINES = ["alpha", "beta"]


def append_line(text):
    LINES.append(text)
    record(("append", text))


def remove_last():
    if not LINES:
        return None
    return LINES.pop()
