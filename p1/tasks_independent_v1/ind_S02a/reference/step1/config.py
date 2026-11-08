"""Config loading."""


import json
from pathlib import Path


DEFAULTS = {"retries": 1, "timeout_s": 10}


def load(path="app_config.json"):
    base = Path(__file__).resolve().parent
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    data = json.loads(target.read_text(encoding="utf-8"))
    out = dict(DEFAULTS)
    out.update(data)
    return out
