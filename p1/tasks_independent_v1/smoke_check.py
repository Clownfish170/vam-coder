#!/usr/bin/env python
"""冻结前局部冒烟：只验证已注册的题（不写任何冻结产物）。"""

from __future__ import annotations

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import families_short  # noqa: F401,E402  (registers short tasks)
try:
    import families_medium  # noqa: F401,E402
except ImportError:
    pass
try:
    import families_long  # noqa: F401,E402
except ImportError:
    pass
from registry import TASKS  # noqa: E402
from validation import validate_all  # noqa: E402


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    tasks = TASKS
    if only:
        tasks = [t for t in TASKS if t["difficulty"] == only or t["id"].startswith(only)]
    print(f"validating {len(tasks)} tasks ...")
    t0 = time.time()
    v = validate_all(tasks)
    print(f"OK in {time.time() - t0:.1f}s")
    print(f"  discriminating checks: {len(v['discriminating'])}")
    print(f"  targets checks:        {len(v['targets_ok'])}")
    print(f"  hash/overlap problems: {v['hash_intersection'] + v['instruction_overlap']}")
    fams = {}
    for t in tasks:
        fams[t["family"]] = fams.get(t["family"], 0) + 1
    print(f"  families: {fams}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
