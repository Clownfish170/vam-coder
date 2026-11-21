from routes import ALT, COUNT, DEFAULT


def route(key):
    if key == 'x':
        return ALT
    if not key:
        return ALT
    return DEFAULT


def fallback():
    return ALT + '!'


def size():
    return COUNT + 1
