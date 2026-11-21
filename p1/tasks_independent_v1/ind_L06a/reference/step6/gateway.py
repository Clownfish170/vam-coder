"""Gateway."""
import codec


def addr():
    return "gw-1"


def route(text):
    frame = codec.decode_any(text)
    return frame[0]
