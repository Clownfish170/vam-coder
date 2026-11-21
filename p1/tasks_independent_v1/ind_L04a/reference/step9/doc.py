"""Line document."""
from journal import record, JOURNAL


LINES = ["alpha", "beta"]
REDO_STACK = []


def append_line(text):
    LINES.append(text)
    record(("append", text))


def remove_last():
    if not LINES:
        return None
    return LINES.pop()


def undo_last():
    if not LINES or not JOURNAL or JOURNAL[-1][0] != "append":
        return None
    kind, text = JOURNAL.pop()
    REDO_STACK.append(text)
    return LINES.pop()


def redo_last():
    if not REDO_STACK:
        return None
    text = REDO_STACK.pop()
    LINES.append(text)
    record(("append", text))
    return text
