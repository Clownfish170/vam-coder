"""Order states."""


def advance(state, action):
    if state in ("shipped", "cancelled"):
        raise ValueError("terminal")
    if state == "new" and action == "pay":
        return "paid"
    if state == "paid" and action == "ship":
        return "shipped"
    if action == "cancel" and can_cancel(state):
        return "cancelled"
    return state


def can_cancel(state):
    return state in ("new", "paid")
