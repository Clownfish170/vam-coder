"""Counter state."""


VALUE = 0


def bump(delta):
    global VALUE
    VALUE += delta
    return VALUE
