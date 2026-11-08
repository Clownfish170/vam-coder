#!/usr/bin/env python
"""P1 任务集物化：从已冻结的 p1_tasks.json + 族定义写出磁盘树，并逐项对照
p1_tasks_manifest.json 校验哈希（只物化，不改任何冻结内容）。"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import p1_registry  # noqa: E402
import p1_families_short, p1_families_medium, p1_families_long  # noqa: F401,E402
from make_p1_tasks import apply_ops, ref_files, write_tree  # noqa: E402


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    manifest = json.loads((HERE / "p1_tasks_manifest.json").read_text(encoding="utf-8"))
    tasks_doc = json.loads((HERE / "p1_tasks.json").read_text(encoding="utf-8"))
    by_id = {t["id"]: t for t in p1_registry.TASKS}
    assert len(by_id) == 48

    problems: list[str] = []
    for entry in manifest["tasks"]:
        tid = entry["id"]
        t = by_id[tid]
        # project
        for rel, content in t["files"].items():
            want = entry["project_files_sha256"][rel]
            if _sha(content.encode("utf-8")) != want:
                problems.append(f"{tid}/{rel}: project hash mismatch vs manifest")
        write_tree(t["files"], HERE / tid / "project")
        # eval + reference
        for i, step in enumerate(t["steps"], 1):
            ev = HERE / tid / "eval" / f"step{i}" / "test_behavior.py"
            ev.parent.mkdir(parents=True, exist_ok=True)
            ev.write_text(step["tests"], encoding="utf-8", newline="\n")
            if _sha(step["tests"].encode("utf-8")) != entry["eval_tests_sha256"][f"step{i}"]:
                problems.append(f"{tid} step{i}: eval hash mismatch")
            rf = ref_files(t, i)
            write_tree(rf, HERE / tid / "reference" / f"step{i}")
            r_agg = _sha(("\n".join(
                f"{k}:{_sha(v.encode('utf-8'))}" for k, v in sorted(rf.items())
            )).encode("utf-8"))
            if r_agg != entry["reference_aggregate_sha256"][f"step{i}"]:
                problems.append(f"{tid} step{i}: reference agg mismatch")

    # holdout_tasks.json 自身哈希复核
    if _sha((HERE / "p1_tasks.json").read_bytes()) != manifest["p1_tasks_sha256"]:
        problems.append("p1_tasks.json sha mismatch vs manifest")

    # 与运行时清单一致性（episodes 数与 id）
    assert len(tasks_doc["episodes"]) == 48
    for e in tasks_doc["episodes"]:
        assert (HERE / e["id"] / "project").is_dir() or not problems

    if problems:
        print("MATERIALIZE VERIFICATION FAILED:")
        for p in problems[:20]:
            print(" -", p)
        return 3
    print("MATERIALIZED + VERIFIED vs frozen manifest: 48 tasks")
    print(f"  root: {HERE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
