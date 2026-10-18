#!/usr/bin/env python
"""生成 P1 冻结清单（不可变）：脚本 / tasks / 各 episode project 与 eval 的 SHA-256。

用法（仓库根目录）：
    python p1/scripts/make_manifest.py --name p1_v0.2_manifest

输出：p1/manifests/<name>.json
- 清单文件已存在时拒绝覆盖（判据/脚本变更 → 新文件名 + 新任务集版本）。
- 不包含 p1/results/（历史 run 原始数据不参与清单）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_p1 import dir_sha256, load_tasks, sha256_file  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 P1 冻结清单")
    ap.add_argument("--name", default="p1_v0.2_manifest")
    ap.add_argument("--tasks", default=str(P1_ROOT / "tasks" / "tasks.json"))
    ap.add_argument("--force", action="store_true",
                    help="覆盖同名清单（仅限清单尚未用于任何正式运行时）")
    args = ap.parse_args()

    tasks_path = Path(args.tasks)
    tasks = load_tasks(tasks_path)
    out_path = P1_ROOT / "manifests" / f"{args.name}.json"
    if out_path.exists() and not args.force:
        print(f"refusing to overwrite existing manifest: {out_path}", file=sys.stderr)
        print("create a NEW manifest name instead (immutable freeze).", file=sys.stderr)
        return 2

    scripts = {}
    for p in sorted((P1_ROOT / "scripts").glob("*.py")):
        scripts[p.name] = sha256_file(p)
    tests = {}
    for p in sorted((P1_ROOT / "tests").glob("*.py")):
        tests[p.name] = sha256_file(p)

    eval_hashes: dict[str, str] = {}
    project_hashes: dict[str, str] = {}
    eval_files: dict[str, dict[str, str]] = {}
    project_files: dict[str, dict[str, str]] = {}
    for ep in tasks["episodes"]:
        ep_root = P1_ROOT / "tasks" / ep["id"]
        proj = ep_root / "project"
        project_hashes[ep["id"]] = dir_sha256(proj)
        project_files[ep["id"]] = {
            str(p.relative_to(proj)).replace("\\", "/"): sha256_file(p)
            for p in sorted(proj.rglob("*")) if p.is_file()
        }
        for step in ep["steps"]:
            key = f"{ep['id']}/{step['id']}"
            eval_dir = ep_root / step["eval"]
            eval_hashes[key] = dir_sha256(eval_dir)
            eval_files[key] = {
                str(p.relative_to(eval_dir)).replace("\\", "/"): sha256_file(p)
                for p in sorted(eval_dir.rglob("*")) if p.is_file()
            }

    manifest = {
        "manifest_version": "p1-v0.2",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "task_set_version": tasks.get("task_set_version"),
        "frozen_at": tasks.get("frozen_at"),
        "tasks_sha256": sha256_file(tasks_path),
        "script_sha256": scripts,
        "test_sha256": tests,
        "eval_dir_sha256": eval_hashes,
        "project_dir_sha256": project_hashes,
        "eval_file_sha256": eval_files,
        "project_file_sha256": project_files,
        "note": (
            "immutable freeze record; regenerate under a NEW name when "
            "scripts/tasks/evals change; historical runs keep their own hashes"
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"manifest -> {out_path}")
    print(f"  task_set_version: {manifest['task_set_version']}")
    print(f"  scripts: {len(scripts)}, evals: {len(eval_hashes)}, "
          f"projects: {len(project_hashes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
