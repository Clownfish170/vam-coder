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


def pack2(seq, cmd, payload):
    return "#" + str(seq) + " " + cmd + ":" + payload


def unpack2(text):
    if not text.startswith("#"):
        raise ValueError("frame2")
    head, rest = text[1:].split(" ", 1)
    if not head.isdigit():
        raise ValueError("seq")
    cmd, payload = rest.split(":", 1)
    return (int(head), cmd, payload)
