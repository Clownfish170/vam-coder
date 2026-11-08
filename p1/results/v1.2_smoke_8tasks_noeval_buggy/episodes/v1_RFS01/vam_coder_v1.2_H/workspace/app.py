from mode import describe


def banner():
    return f"mode={describe()}"

def is_active():
    """Return True if the mode is active."""
    return describe() == "active"
