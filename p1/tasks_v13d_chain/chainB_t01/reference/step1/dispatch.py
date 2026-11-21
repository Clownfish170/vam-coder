from routes import ALT, DEFAULT


def route(key):
    if key == '':
        return ALT
    return DEFAULT


def fallback():
    return ALT
