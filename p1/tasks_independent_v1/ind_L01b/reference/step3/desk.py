"""Dispatch desk."""
from rules import MIN_LEVEL, MAX_LEVEL


BUCKETS = {}


def admit(job, level):
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
