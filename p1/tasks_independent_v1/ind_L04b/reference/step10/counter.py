"""Counter state."""
from ops_log import push, OPS, UNDONE


VALUE = 0


def bump(delta):
    if delta == 0:
        raise ValueError("delta")
    global VALUE
    VALUE += delta
    push({"op": "bump", "delta": delta})
    return VALUE


def get():
    return VALUE


def undo_last():
    global VALUE
    if not OPS:
        return None
    op = OPS.pop()
    if op["op"] == "bump":
        VALUE -= op["delta"]
    UNDONE.append(op)
    return op


def redo_last():
    if not UNDONE:
        return None
    op = UNDONE.pop()
    return bump(op["delta"])
