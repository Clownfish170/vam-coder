"""Bridge."""
import wire


def name():
    return "bridge-0"


def dispatch(text):
    try:
        cmd, payload = wire.unpack(text)
        wire.fields(payload)
        return cmd
    except ValueError:
        return None
