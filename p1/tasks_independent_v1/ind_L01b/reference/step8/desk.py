"""Dispatch desk."""
from rules import DEFAULT_LEVEL, MIN_LEVEL, MAX_LEVEL


BUCKETS = {}


def admit(job, level=None):
    if level is None:
        level = DEFAULT_LEVEL
    if level < MIN_LEVEL:
        level = MIN_LEVEL
    if level > MAX_LEVEL:
        level = MAX_LEVEL
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


def levels():
    return sorted((lvl for lvl, jobs in BUCKETS.items() if jobs), reverse=True)
