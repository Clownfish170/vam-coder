"""Job queue."""
from policy import MIN_PRIO, CAP


QUEUE = []
SEQ = 0


def push(job, prio):
    if prio < MIN_PRIO:
        raise ValueError("prio")
    if len(QUEUE) >= CAP:
        raise ValueError("full")
    global SEQ
    SEQ += 1
    QUEUE.append((job, prio, SEQ))


def pop():
    if not QUEUE:
        return None
    QUEUE.sort(key=lambda t: (-t[1], t[0]))
    return QUEUE.pop(0)[0]


def bump(job, prio):
    for i, t in enumerate(QUEUE):
        if t[0] == job:
            QUEUE[i] = (job, prio, t[2])
            return True
    return False


def take(n):
    out = []
    for _ in range(n):
        job = pop()
        if job is None:
            break
        out.append(job)
    return out
