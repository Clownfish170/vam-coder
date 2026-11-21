"""Desk console."""
from desk import BUCKETS


def show(job):
    return f"job={job}"


def board():
    return {lvl: len(jobs) for lvl, jobs in BUCKETS.items()}
