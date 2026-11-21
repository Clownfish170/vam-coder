"""Job queue."""
from policy import MIN_PRIO


QUEUE = []
SEQ = 0


def push(job, prio):
    if prio < MIN_PRIO:
        raise ValueError("prio")
    global SEQ
    SEQ += 1
    QUEUE.append((job, prio, SEQ))


def pop():
    if not QUEUE:
        return None
    QUEUE.sort(key=lambda t: (-t[1], t[2]))
    return QUEUE.pop(0)[0]
