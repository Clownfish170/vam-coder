"""Wire format."""


def pack(cmd, payload):
    return cmd + ":" + payload


def unpack(text):
    cmd, payload = text.split(":", 1)
    return cmd, payload
