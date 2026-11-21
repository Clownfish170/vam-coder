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
