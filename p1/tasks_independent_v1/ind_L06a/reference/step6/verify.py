"""Frame checks."""
import codec


def kind_of(text):
    return text.split("|", 1)[0]


def check(text):
    try:
        codec.decode_any(text)
        return True
    except ValueError:
        return False
