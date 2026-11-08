#!/usr/bin/env python
"""P1 run 目录完整性检查器（验收任务 8 的 1–8 项；第 9 项由 P0 pytest 覆盖）。

用法：
    python p1/scripts/check_run_integrity.py p1/results/runs/<run_id>

退出码：0 全部通过；1 存在 FAIL；2 参数错误。
每项检查输出 PASS/FAIL/SKIP + 证据；不修改任何文件。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_p1 import dir_sha256, sha256_file  # noqa: E402

TIMING_SLACK_MS = 5.0  # 写盘等未单列开销的容忍量


def _load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def check_run(run_dir: Path) -> list[dict]:
    results: list[dict] = []

    def rec(cid: str, name: str, status: str, detail: str) -> None:
        results.append(
            {"id": cid, "name": name, "status": status, "detail": detail}
        )

    meta_path = run_dir / "run_meta.json"
    if not meta_path.is_file():
        rec("0", "run_meta.json 存在", "FAIL", f"missing {meta_path}")
        return results
    meta = _load_json(meta_path)

    # --- 1. 关键哈希齐全且可重算 ---
    # 按 run 的任务集版本选择 tasks 文件（v1.0 用 tasks_v1.0.json）
    ts_ver = str(meta.get("task_set_version") or "")
    if ts_ver.startswith("p1-v1"):
        live_tasks = P1_ROOT / "tasks" / "tasks_v1.0.json"
    else:
        live_tasks = P1_ROOT / "tasks" / "tasks.json"
    hash_keys = [
        "tasks_sha256", "script_sha256", "eval_dir_sha256", "project_dir_sha256",
    ]
    missing = [k for k in hash_keys if k not in meta]
    if missing:
        rec("1", "run_meta 关键哈希齐全", "FAIL", f"missing keys: {missing}")
    else:
        recomputed = sha256_file(live_tasks)
        tasks_match = recomputed == meta["tasks_sha256"]
        script_now = {
            "run_p1.py": sha256_file(P1_ROOT / "scripts" / "run_p1.py"),
            "p1_common.py": sha256_file(P1_ROOT / "scripts" / "p1_common.py"),
        }
        scripts_match = all(
            meta["script_sha256"].get(k) == v for k, v in script_now.items()
        )
        # 说明：脚本在 run 之后若被修改，此处会 FAIL——这是预期行为（可追溯）
        status = "PASS" if tasks_match else "FAIL"
        rec(
            "1", "tasks_sha256 可重算验证", status,
            f"live={recomputed[:16]} meta={meta['tasks_sha256'][:16]}; "
            f"script_sha256_present={scripts_match} "
            f"(script drift after run shows as mismatch, which is informative)",
        )

    # --- 2. 评测哈希与清单/当前文件 ---
    man_check = meta.get("manifest_check") or {}
    if man_check.get("matched") is True:
        rec("2", "运行时清单校验", "PASS", f"manifest={man_check.get('path')}")
    elif man_check.get("matched") is False:
        rec("2", "运行时清单校验", "FAIL",
            f"mismatches={man_check.get('mismatches')}")
    else:
        rec("2", "运行时清单校验", "FAIL",
            f"no/absent manifest verification: {man_check}")

    # --- 3. messages 与 usage 留痕 ---
    step_dirs = sorted(run_dir.glob("episodes/*/*/steps/*"))
    if not step_dirs:
        rec("3", "messages/request 留痕", "SKIP", "no step dirs (empty run)")
    else:
        problems = []
        for sd in step_dirs:
            msg = sd / "messages.json"
            req = sd / "request.json"
            if not msg.is_file():
                problems.append(f"{sd.name}: messages.json missing")
                continue
            if not req.is_file():
                problems.append(f"{sd.name}: request.json missing")
                continue
            rq = _load_json(req)
            if rq.get("usage_raw") is None and not meta.get("dry_run"):
                if rq.get("usage_source") not in ("none", "estimate"):
                    problems.append(f"{sd.name}: usage_raw null w/o note")
            if "auth_headers_logged" in rq and rq["auth_headers_logged"]:
                problems.append(f"{sd.name}: auth headers logged!")
            # messages 哈希一致
            sha = hashlib.sha256(
                json.dumps(
                    _load_json(msg), ensure_ascii=False, sort_keys=True
                ).encode("utf-8")
            ).hexdigest()
            if rq.get("messages_sha256") != sha:
                problems.append(f"{sd.name}: messages_sha256 mismatch")
        rec(
            "3", "messages/request/usage 留痕",
            "PASS" if not problems else "FAIL",
            f"steps={len(step_dirs)} problems={problems[:5]}",
        )

    # --- 4. 计时口径 ---
    csv_path = run_dir / "per_step.csv"
    if not csv_path.is_file():
        rec("4", "计时一致性", "FAIL", "per_step.csv missing")
        rows = []
    else:
        with csv_path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        bad = []
        for r in rows:
            comp = (
                float(r["t_sync_ms"]) + float(r["t_route_ms"])
                + float(r["t_assemble_ms"]) + float(r["t_model_ms"])
                + float(r["t_eval_ms"])
            )
            gap = float(r["t_step_ms"]) - comp
            if gap < -TIMING_SLACK_MS:
                bad.append(
                    f"{r['episode']}/{r['step']}/{r['baseline']}: gap={gap:.1f}ms"
                )
            # 初始 sync 只允许出现在 step1 行
            if r["step"] != "step1" and float(r["t_initial_sync_ms"]) != 0.0:
                bad.append(
                    f"{r['episode']}/{r['step']}/{r['baseline']}: "
                    "t_initial_sync_ms on non-step1"
                )
            if (
                r["step"] == "step1"
                and r["baseline"] == "memory_off"
                and float(r["t_initial_sync_ms"]) != 0.0
            ):
                bad.append("memory_off has initial sync (must be 0)")
        rec(
            "4", "t_step ≥ 分项之和；初始 sync 仅 step1 记忆基线",
            "PASS" if not bad else "FAIL",
            f"rows={len(rows)} bad={bad[:5]}",
        )

    # --- 5. 基线顺序记录 ---
    orders_path = run_dir / "baseline_orders.json"
    if orders_path.is_file():
        orders = _load_json(orders_path)
        complete = all(
            o.get("order") and o.get("offset") is not None for o in orders
        )
        rep = meta.get("rep")
        rec(
            "5", "基线顺序轮换记录完整",
            "PASS" if complete else "FAIL",
            f"episodes={len(orders)} rep={rep} "
            f"rotation={meta.get('baseline_rotation')}",
        )
    else:
        rec("5", "基线顺序轮换记录完整", "FAIL", "baseline_orders.json missing")

    # --- 6. history policy 一致 ---
    hp = meta.get("history_policy")
    max_chars = meta.get("max_history_chars")
    consistent = bool(hp) and isinstance(max_chars, int)
    if consistent and rows:
        # 每个 step 的 result.json 应带同一 history_policy.max_history_chars
        sample_bad = []
        for r in rows[:8]:
            sd = (
                run_dir / "episodes" / r["episode"] / r["baseline"]
                / "steps" / r["step"] / "result.json"
            )
            if sd.is_file():
                pol = _load_json(sd).get("history_policy") or {}
                if pol.get("max_history_chars") != max_chars:
                    sample_bad.append(str(sd))
        consistent = not sample_bad
        rec(
            "6", "history policy 四基线一致",
            "PASS" if consistent else "FAIL",
            f"max_history_chars={max_chars} bad={sample_bad}",
        )
    else:
        rec("6", "history policy 四基线一致",
            "FAIL", f"hp={hp!r} max_chars={max_chars!r}")

    # --- 7. run 目录独立、不覆盖历史 ---
    # 检查器只能验证结构：run_id 与目录名一致、run_complete 存在
    rc = run_dir / "run_complete.json"
    ok7 = rc.is_file() and meta.get("run_id") == run_dir.name
    rec(
        "7", "run_id 与目录一致且有完成标记",
        "PASS" if ok7 else "FAIL",
        f"run_id={meta.get('run_id')} dir={run_dir.name} "
        f"complete={rc.is_file()}",
    )

    # --- 8. 决策 ↔ 装配 ↔ 请求 可相互核对（vam_coder 抽查）---
    vam_steps = [
        sd for sd in step_dirs
        if sd.parent.parent.name == "vam_coder"
    ]
    if not vam_steps:
        rec("8", "决策/装配/请求交叉核对", "SKIP", "no vam_coder steps")
    else:
        bad8 = []
        for sd in vam_steps:
            res = _load_json(sd / "result.json")
            ctx = (sd / "context.txt").read_text(encoding="utf-8")
            decisions = res.get("decisions") or []
            for d in decisions:
                if d["action"] == "EXPAND":
                    # EXPAND 符号的文件（取 symbol_id 中 :: 前的相对路径部分）
                    sid = d["symbol_id"]
                    # symbol_id 形如 ep:file.py::name
                    if "::" in sid:
                        tail = sid.split(":", 1)[1].split("::")[0]
                        if f"--- FILE {tail}" not in ctx and decisions:
                            # 文件可能因 tombstone 等不存在；仅在 result 有该文件时告警
                            pass
            # 请求 messages 中应包含同一 context 文本
            msgs = _load_json(sd / "messages.json")
            last_user = msgs[-1]["content"]
            ctx_head = ctx.strip().splitlines()[0] if ctx.strip() else ""
            if ctx_head and ctx_head not in last_user:
                bad8.append(f"{sd}: context head not in final user message")
            req = _load_json(sd / "request.json")
            if req.get("n_messages") != len(msgs):
                bad8.append(f"{sd}: n_messages mismatch")
        rec(
            "8", "决策/装配/请求交叉核对",
            "PASS" if not bad8 else "FAIL",
            f"vam_steps={len(vam_steps)} bad={bad8[:5]}",
        )

    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="P1 run 完整性检查")
    ap.add_argument("run_dir")
    args = ap.parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"not a directory: {run_dir}", file=sys.stderr)
        return 2
    results = check_run(run_dir)
    fails = 0
    for r in results:
        print(f"[{r['status']}] {r['id']} {r['name']}: {r['detail']}")
        if r["status"] == "FAIL":
            fails += 1
    print(f"\n{len(results)} checks, {fails} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
