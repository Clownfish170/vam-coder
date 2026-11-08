"""Order states."""


def advance(state, action):
    if state == "new" and action == "pay":
        return "paid"
    if state == "paid" and action == "ship":
        return "shipped"
    return state


def can_cancel(state):
    return state in ("new", "paid")
