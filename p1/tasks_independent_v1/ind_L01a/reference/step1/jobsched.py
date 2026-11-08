"""Job queue."""


QUEUE = []
SEQ = 0


def push(job, prio):
    global SEQ
    SEQ += 1
    QUEUE.append((job, prio, SEQ))


def pop():
    if not QUEUE:
        return None
    QUEUE.sort(key=lambda t: (-t[1], t[2]))
    return QUEUE.pop(0)[0]
