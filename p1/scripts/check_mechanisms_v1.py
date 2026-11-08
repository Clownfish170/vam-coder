#!/usr/bin/env python
"""P1-v1.0 机制检查器（Q3a/Q3b）：读取预声明表（哈希锁定）并合取判定。

用法：
    python p1/scripts/check_mechanisms_v1.py \
        --run p1/results/runs/<run_id> \
        --predecl p1/tasks/predeclared_mechanisms_v1.0.json \
        [--expected-hash <sha256>]
退出码：0 无必需事件缺失；1 有缺失；2 参数/哈希错误。
输出：stdout 摘要 + <run>/mechanism_check.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slice_invalidation_by_step(log_path: Path) -> dict[str, list[dict]]:
    """按 sync_completed 边界切片：第 k 个 sync 之前的事件属 step_k。"""
    steps: dict[str, list[dict]] = {"step1": [], "step2": []}
    if not log_path.is_file():
        return steps
    sync_idx = 0
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        name = ev.get("event")
        if name == "sync_completed":
            sync_idx += 1
            continue
        key = f"step{min(sync_idx + 1, 2)}"
        steps[key].append(ev)
    return steps


def match_event(entry: dict, events: list[dict]) -> bool:
    want_file = entry["target_file"]
    want_sym = entry.get("target_symbol", "*")
    kind = entry["kind"]
    event = entry["event"]
    for ev in events:
        if kind == "absence":
            sid = ev.get("symbol_id", "") or ""
            file_part = sid.split(":", 1)[1].split("::")[0] if ":" in sid else ""
            if event != "any" and ev.get("event") != event:
                continue
            if file_part == want_file:
                return True  # absence violated (event found)
            continue
        if ev.get("event") != event:
            continue
        sid = ev.get("symbol_id", "")
        if ":" not in sid or "::" not in sid:
            continue
        file_part = sid.split(":", 1)[1].split("::")[0]
        sym_part = sid.split("::")[1]
        if file_part != want_file:
            continue
        # 方法符号形如 Client.fetch：允许按全名或末段匹配（rev3.2 目标绑定）
        if want_sym not in ("*", "") and sym_part != want_sym \
                and sym_part.split(".")[-1] != want_sym:
            continue
        return True
    return False


def check_run(run_dir: Path, predecl_path: Path, expected_hash: str | None) -> dict:
    live_hash = sha256_file(predecl_path)
    if expected_hash and live_hash != expected_hash:
        raise SystemExit(
            f"PREDECL HASH MISMATCH: expected {expected_hash} live {live_hash}"
        )
    predecl = json.loads(predecl_path.read_text(encoding="utf-8"))
    entries = predecl["entries"]
    results = []
    any_fail = False
    for ep_dir in sorted((run_dir / "episodes").iterdir()):
        task_id = ep_dir.name
        vam = ep_dir / "vam_coder"
        if not vam.is_dir():
            continue
        by_step = slice_invalidation_by_step(vam / "logs" / "invalidation_events.jsonl")
        task_entries = [e for e in entries if e["task_id"] == task_id]
        entry_results = []
        req_ok = True
        for e in task_entries:
            step_events = by_step.get(e["step"], [])
            if e["kind"] == "omission":
                res_json = vam / "steps" / e["step"] / "result.json"
                n = 0
                if res_json.is_file():
                    n = json.loads(res_json.read_text(encoding="utf-8")).get(
                        "n_verified_safe_omissions", 0
                    )
                ok = n >= int(e.get("min_count", 1))
                entry_results.append({
                    "entry": e, "matched": ok, "observed_n": n,
                })
                if e["required"] and not ok:
                    req_ok = False
                continue
            matched = match_event(e, step_events)
            if e["kind"] == "absence":
                ok = not matched  # absence passes when no matching event
                entry_results.append({"entry": e, "absence_violated": matched})
                if e["required"] and not ok:
                    req_ok = False
                continue
            entry_results.append({"entry": e, "matched": matched})
            if e["required"] and not matched:
                req_ok = False
        if task_entries and not req_ok:
            any_fail = True
        results.append({
            "task_id": task_id,
            "q3a_q3b_pass": req_ok if any(
                x["entry"]["required"] for x in entry_results
            ) else None,
            "entries": [
                {
                    "step": r["entry"]["step"],
                    "kind": r["entry"]["kind"],
                    "event": r["entry"]["event"],
                    "target": f"{r['entry']['target_file']}::{r['entry'].get('target_symbol','*')}",
                    "required": r["entry"]["required"],
                    "result": {k: v for k, v in r.items() if k != "entry"},
                }
                for r in entry_results
            ],
        })
    out = {
        "predeclared_sha256": live_hash,
        "predeclared_path": str(predecl_path),
        "tasks": results,
        "all_required_passed": not any_fail,
    }
    (run_dir / "mechanism_check.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--predecl", required=True)
    ap.add_argument("--expected-hash", default="")
    args = ap.parse_args()
    run_dir = Path(args.run)
    predecl = Path(args.predecl)
    if not run_dir.is_dir() or not predecl.is_file():
        print("missing run dir or predecl", file=sys.stderr)
        return 2
    out = check_run(run_dir, predecl, args.expected_hash or None)
    print(f"predecl sha256 = {out['predeclared_sha256']}")
    for t in out["tasks"]:
        flag = "n/a" if t["q3a_q3b_pass"] is None else (
            "PASS" if t["q3a_q3b_pass"] else "FAIL"
        )
        print(f"[{flag}] {t['task_id']}")
        for e in t["entries"]:
            if e["required"]:
                print(f"    REQ {e['step']} {e['kind']}:{e['event']} "
                      f"{e['target']} -> {e['result']}")
    print(f"all_required_passed={out['all_required_passed']}")
    return 1 if not out["all_required_passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
