"""Player states."""


def on_event(state, event):
    if state == "ended":
        raise ValueError("ended")
    if state == "idle" and event == "play":
        return "buffering"
    if state == "buffering" and event == "ready":
        return "playing"
    if state == "playing" and event == "pause":
        return "paused"
    if state == "paused" and event == "play":
        return "playing"
    if state in ("playing", "paused") and event == "stop":
        return "idle"
    if state == "playing" and event == "finish":
        return "ended"
    return state


def is_playing(state):
    return state == "playing"


def available_events(state):
    if state == "ended":
        return []
    if state == "idle":
        return ["play"]
    if state == "buffering":
        return ["ready"]
    if state == "playing":
        return ["pause", "stop", "finish"]
    if state == "paused":
        return ["play", "stop"]
    return []
