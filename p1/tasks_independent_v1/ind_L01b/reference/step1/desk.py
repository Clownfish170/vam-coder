"""Dispatch desk."""


BUCKETS = {}


def admit(job, level):
    BUCKETS.setdefault(level, []).append(job)


def next_job():
    for lvl in sorted(BUCKETS, reverse=True):
        if BUCKETS[lvl]:
            return BUCKETS[lvl].pop(0)
    return None
