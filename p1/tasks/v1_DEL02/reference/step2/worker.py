from queue import push, p


def work(items, x):
    push(items, x)
    return p(items)


def drain(items):
    count = 0
    while items:
        p(items)
        count += 1
    return count
