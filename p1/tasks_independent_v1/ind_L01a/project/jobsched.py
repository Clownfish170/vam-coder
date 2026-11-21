"""Job queue."""


QUEUE = []


def push(job, prio):
    QUEUE.append((job, prio))


def pop():
    if not QUEUE:
        return None
    return QUEUE.pop(0)[0]
