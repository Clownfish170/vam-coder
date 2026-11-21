"""Dispatch desk."""
from rules import DEFAULT_LEVEL, MIN_LEVEL, MAX_LEVEL


BUCKETS = {}


def admit(job, level=None):
    if level is None:
        level = DEFAULT_LEVEL
    if level < MIN_LEVEL or level > MAX_LEVEL:
        raise ValueError("level")
    BUCKETS.setdefault(level, []).append(job)


def next_job():
    for lvl in sorted(BUCKETS, reverse=True):
        if BUCKETS[lvl]:
            return BUCKETS[lvl].pop(0)
    return None


def count(level):
    return len(BUCKETS.get(level, []))


def drain(level, n):
    out = []
    bucket = BUCKETS.get(level, [])
    limit = min(n, len(bucket))
    for _ in range(limit):
        out.append(bucket.pop(0))
    return out
