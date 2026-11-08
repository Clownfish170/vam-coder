"""Server config."""


import json
from pathlib import Path


DEFAULTS = {"host": "0.0.0.0", "port": 80, "workers": 1}


def load(path="server.json"):
    base = Path(__file__).resolve().parent
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    data = json.loads(target.read_text(encoding="utf-8"))
    out = dict(DEFAULTS)
    out.update(data)
    return out
