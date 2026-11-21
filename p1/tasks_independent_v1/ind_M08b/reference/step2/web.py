"""Web glue."""

from routes import bind, serve


def index(payload):
    return f"index:{payload}"


bind("/", index)
