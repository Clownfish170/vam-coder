"""Guard rails."""
import wire


def is_safe(text):
    try:
        cmd, payload = wire.unpack(text)
        wire.fields(payload)
        return True
    except ValueError:
        return False
