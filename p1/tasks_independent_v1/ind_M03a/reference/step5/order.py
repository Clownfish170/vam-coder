"""Order states."""


def advance(state, action):
    if state in ("cancelled", "refunded"):
        raise ValueError("terminal")
    if state == "new" and action == "pay":
        return "paid"
    if state == "paid" and action == "ship":
        return "shipped"
    if state == "shipped":
        if action == "refund":
            return "refunded"
        raise ValueError("bad action")
    if action == "cancel" and can_cancel(state):
        return "cancelled"
    return state


def can_cancel(state):
    return state in ("new", "paid")


def available_actions(state):
    if state in ("cancelled", "refunded"):
        return []
    if state == "new":
        return ["pay", "cancel"]
    if state == "paid":
        return ["ship", "cancel"]
    if state == "shipped":
        return ["refund"]
    return []
