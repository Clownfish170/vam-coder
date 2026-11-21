from routes import ALT, COUNT, DEFAULT


def route(key):
    if not key:
        return ALT
    return DEFAULT


def fallback():
    return COUNT


def size():
    return COUNT * 2
