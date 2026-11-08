"""Shell front."""
import plug


def prompt():
    return ">"


def run(name, *args):
    try:
        return plug.dispatch(name, *args)
    except KeyError:
        return f"err:{name}"
