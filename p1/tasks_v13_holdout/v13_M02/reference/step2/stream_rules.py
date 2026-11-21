"""Rule definitions for streams."""


def dedupe(msgs):
    seen = []
    for m in msgs:
        if m not in seen:
            seen.append(m)
    return seen


def normalize(msgs):
    return [m.lower() if isinstance(m, str) else m for m in msgs]
