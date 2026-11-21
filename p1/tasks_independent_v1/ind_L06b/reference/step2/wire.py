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


def fields(payload):
    out = {}
    for seg in payload.split(";"):
        if "=" not in seg:
            raise ValueError("field")
        k, v = seg.split("=", 1)
        out[k] = v
    return out
