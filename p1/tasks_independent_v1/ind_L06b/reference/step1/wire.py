"""Wire format."""


def pack(cmd, payload):
    return cmd + ":" + payload


def unpack(text):
    if ":" not in text:
        raise ValueError("frame")
    cmd, payload = text.split(":", 1)
    if not payload.strip():
        raise ValueError("payload")
    return cmd, payload
