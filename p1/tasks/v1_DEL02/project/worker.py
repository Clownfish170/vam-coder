from queue import push, p


def work(items, x):
    push(items, x)
    return p(items)
