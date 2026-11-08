"""Counter state."""
from ops_log import push


VALUE = 0


def bump(delta):
    global VALUE
    VALUE += delta
    push({"op": "bump", "delta": delta})
    return VALUE


def get():
    return VALUE
