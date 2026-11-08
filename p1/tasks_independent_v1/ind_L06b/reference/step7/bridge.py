"""Bridge."""
import wire


def name():
    return "bridge-0"


def dispatch(text):
    try:
        frame = wire.unpack_any(text)
        cmd = frame[1] if len(frame) == 3 else frame[0]
        wire.fields(frame[-1])
        return cmd
    except ValueError:
        return None
