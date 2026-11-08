"""Queue report."""
from jobsched import QUEUE


def size_line(n):
    return f"size={n}"


def preview():
    if not QUEUE:
        return None
    ordered = sorted(QUEUE, key=lambda t: (-t[1], t[2]))
    return ordered[0][0]
