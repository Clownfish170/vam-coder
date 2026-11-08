"""Player states."""


def on_event(state, event):
    if state == "idle" and event == "play":
        return "playing"
    if state == "playing" and event == "pause":
        return "paused"
    if state == "paused" and event == "play":
        return "playing"
    if state in ("playing", "paused") and event == "stop":
        return "idle"
    return state


def is_playing(state):
    return state == "playing"
