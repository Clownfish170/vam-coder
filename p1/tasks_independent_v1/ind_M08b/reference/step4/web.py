"""Web glue."""

from routes import bind, serve


def index(payload):
    return f"index:{payload}"


def health(payload):
    return "up"


bind("/", index)
bind("/health", health)
