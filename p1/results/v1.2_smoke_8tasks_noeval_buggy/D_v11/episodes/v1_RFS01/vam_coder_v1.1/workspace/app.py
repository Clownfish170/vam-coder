from mode import describe


def banner():
    return f"mode={describe()}"

def is_active():
    return describe() == "active"
