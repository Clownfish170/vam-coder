from mode import describe, is_active


def banner():
    return f"mode={describe() if is_active() else 'inactive'}"
