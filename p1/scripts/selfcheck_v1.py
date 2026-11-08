#!/usr/bin/env python
"""P1-v1.0 参考补丁自检：初始仓库 eval 必须失败；应用参考补丁后必须通过。

用法：python p1/scripts/selfcheck_v1.py [--tasks p1/tasks/tasks_v1.0.json]
退出码：0=24/48 全过；1=有失败；2=参数错误。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from p1_common import run_eval  # noqa: E402


def apply_reference(ref_dir: Path, workspace: Path) -> None:
    delete_marker = ref_dir / "__DELETE__.json"
    for p in ref_dir.rglob("*"):
        if not p.is_file() or p.name == "__DELETE__.json":
            continue
        rel = p.relative_to(ref_dir)
        target = workspace / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
    if delete_marker.is_file():
        for rel in json.loads(delete_marker.read_text(encoding="utf-8")):
            victim = workspace / rel
            if victim.exists():
                victim.unlink()


def check_task(task_id: str, tasks_dir: Path) -> list[dict]:
    root = tasks_dir / task_id
    results: list[dict] = []
    for step in ("step1", "step2"):
        ws = Path(tempfile.mkdtemp(prefix=f"sc_{task_id}_{step}_"))
        try:
            shutil.copytree(root / "project", ws, dirs_exist_ok=True)
            if step == "step2":
                apply_reference(root / "reference" / "step1", ws)
            ok_init, _ = run_eval(ws, root / "eval" / step)
            apply_reference(root / "reference" / step, ws)
            ok_patched, out = run_eval(ws, root / "eval" / step)
            passed = (ok_init is False) and (ok_patched is True)
            results.append({
                "task": task_id, "step": step,
                "initial_failed": ok_init is False,
                "patched_passed": ok_patched is True,
                "passed": passed,
                "patched_output_tail": out.strip().splitlines()[-1] if out.strip() else "",
            })
        finally:
            shutil.rmtree(ws, ignore_errors=True)
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=str(P1_ROOT / "tasks" / "tasks_v1.0.json"))
    args = ap.parse_args()
    tasks_path = Path(args.tasks)
    if not tasks_path.is_file():
        print(f"missing {tasks_path}", file=sys.stderr)
        return 2
    doc = json.loads(tasks_path.read_text(encoding="utf-8"))
    tasks_dir = tasks_path.parent
    all_results: list[dict] = []
    for ep in doc["episodes"]:
        rows = check_task(ep["id"], tasks_dir)
        all_results.extend(rows)
        for r in rows:
            flag = "PASS" if r["passed"] else "FAIL"
            print(
                f"[{flag}] {r['task']}/{r['step']} "
                f"initial_failed={r['initial_failed']} "
                f"patched_passed={r['patched_passed']} "
                f"{r['patched_output_tail']}"
            )
    n_pass = sum(1 for r in all_results if r["passed"])
    print(f"\n{n_pass}/{len(all_results)} checks passed")
    report = P1_ROOT / "results" / "selfcheck_v1_report.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps({"total": len(all_results), "passed": n_pass,
                    "results": all_results}, indent=2),
        encoding="utf-8",
    )
    return 0 if n_pass == len(all_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
