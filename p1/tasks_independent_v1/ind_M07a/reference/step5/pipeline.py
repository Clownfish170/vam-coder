"""Data pipeline."""

import json
from pathlib import Path


def load_config(path="config.json"):
    base = Path(__file__).resolve().parent
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    return json.loads(target.read_text(encoding="utf-8"))


def default_stages():
    return load_config()["stages"]


def run(rows, stages=None):
    if stages is None:
        stages = default_stages()
    out = list(rows)
    for name in stages:
        if name == "load":
            out = list(out)
        elif name == "clean":
            out = [r for r in out if r]
        elif name == "trim":
            out = [r.strip() if isinstance(r, str) else r for r in out]
        elif name == "count":
            out = [len(out)]
        else:
            raise ValueError(name)
    return out
