"""Order states."""


def advance(state, action):
    if state == "new" and action == "pay":
        return "paid"
    return state


def can_cancel(state):
    return state in ("new", "paid")
