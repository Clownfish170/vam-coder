"""Metric flow."""

import json
from pathlib import Path


def read_settings(path="settings.json"):
    base = Path(__file__).resolve().parent
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    return json.loads(target.read_text(encoding="utf-8"))


def default_flow():
    return read_settings()["flow"]


def execute(rows, flow=None):
    if flow is None:
        flow = default_flow()
    out = list(rows)
    for name in flow:
        if name == "read":
            out = list(out)
        elif name == "dedupe":
            seen = set()
            out = [r for r in out if not (r in seen or seen.add(r))]
        elif name == "upper":
            out = [r.upper() if isinstance(r, str) else r for r in out]
        else:
            raise ValueError(name)
    return out
