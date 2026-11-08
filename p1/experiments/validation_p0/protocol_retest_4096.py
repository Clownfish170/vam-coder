#!/usr/bin/env python
"""第5项：协议违规受控复测——对 protocol_attribution 判定的 EMPTY_TRUNC 涉事 episode，
以 max_tokens=4096 在隔离目录按【原架构/原任务清单】各重跑一次（不触碰任何冻结实验目录）。

判定：复测后每步响应含 FILE:/NO_EDIT（或至少无触顶空输出）→ resolved。
输出：protocol_retest_4096/runs/<round>/<ep_id>/、retest_log.jsonl、retest_results.csv、retest_summary.json。
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent          # validation_p0
P1 = HERE.parents[1]
ROOT = P1.parent
ATTR = HERE / "protocol_attribution.csv"

TASKS_V13 = P1 / "tasks_v13_holdout" / "holdout_tasks.json"
TASKS_P1 = P1 / "tasks_p1_validation" / "p1_tasks.json"
ROUND_TASKS = {
    "round1_holdout": TASKS_V13,
    "round2_v13b": TASKS_P1,
    "round3_deepseek": TASKS_P1,
    "p1_confirmatory": TASKS_P1,
    "p2_ablation": TASKS_P1,
}

# arch（最长优先）→ (runner, arm/baseline, extra_flags)
ARCH_MAP = [
    ("vam_coder_v1.2_F_ablate_history_redact", "v12", "F", ["--history-policy", "redact"]),
    ("vam_coder_v1.2_F_ablate_no_must_closure", "v12", "F", ["--no-must-closure"]),
    ("vam_coder_v1.2_E_ablate_no_must_closure", "v12", "E", ["--no-must-closure"]),
    ("vam_coder_v1.2_F_ablate_no_oprime", "v12", "F", ["--no-oprime"]),
    ("vam_coder_v1.3_V13A", "v12", "V13A", []),
    ("vam_coder_v1.3_V13B", "v12", "V13B", []),
    ("vam_coder_v1.2_F", "v12", "F", []),
    ("vam_coder_v1.2_E", "v12", "E", []),
    ("vam_coder_v1.2_H", "v12", "H", []),
    ("memory_off", "p1", "memory_off", []),
    ("symbol_full_read", "p1", "symbol_full_read", []),
]


def parse_arch(ep_id: str):
    for a, runner, arm, extra in ARCH_MAP:
        if f"_{a}_" in ep_id:
            return a, runner, arm, extra
    raise ValueError(ep_id)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="https://maas.qianwenaiapi.com/compatible-mode/v1")
    ap.add_argument("--model", default="deepseek-v4.1-flash-1017")
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--out", default=str(HERE / "protocol_retest_4096"))
    args = ap.parse_args(argv)

    # 归因表 → 唯一涉事 episode
    attr = list(csv.DictReader(ATTR.open(encoding="utf-8")))
    eps: dict[tuple, dict] = {}
    for r in attr:
        key = (r["round"], r["episode_id"])
        e = eps.setdefault(key, {
            "round": r["round"], "episode_id": r["episode_id"],
            "task_id": r["task_id"], "architecture": r["architecture"],
            "before_classes": [],
        })
        e["before_classes"].append(r["class"])
    print(f"unique episodes to retest: {len(eps)}")

    out_root = Path(args.out)
    runs = out_root / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    log_path = out_root / "retest_log.jsonl"
    done = set()
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                if rec.get("status") == "OK":
                    done.add(rec["episode_id"])
            except json.JSONDecodeError:
                continue

    results = []
    n_new = 0
    for (round_name, ep_id), meta in sorted(eps.items()):
        if ep_id in done:
            continue
        task, arch_full = meta["task_id"], meta["architecture"]
        arch, runner, arm, extra = parse_arch(ep_id)
        rep = int(ep_id.rsplit("_R", 1)[1])
        tasks_json = ROUND_TASKS[round_name]
        ep_out = runs / round_name / ep_id
        ep_out.mkdir(parents=True, exist_ok=True)
        if runner == "v12":
            cmd = [
                sys.executable, str(P1 / "scripts" / "run_p1_v12.py"),
                "--episode", task, "--arm", arm, "--rep", str(rep),
                "--tasks-json", str(tasks_json), "--out-root", str(ep_out / "runner_out"),
                "--pause-seconds", "0", "--closure-depth", "2",
                "--endpoint", args.endpoint, "--model", args.model,
                "--temperature", "0", "--seed", "0",
                "--max-tokens", str(args.max_tokens),
                *extra,
            ]
        else:
            cmd = [
                sys.executable, str(P1 / "scripts" / "run_p1.py"),
                "--tasks", str(tasks_json),
                "--episode", task, "--baselines", arm,
                "--rep", str(rep), "--out", str(ep_out / "runner_out"),
                "--pause-seconds", "0",
                "--endpoint", args.endpoint, "--model", args.model,
                "--temperature", "0", "--seed", "0",
                "--max-tokens", str(args.max_tokens),
                "--history-policy", "keep",
                "--allow-manifest-mismatch", "--no-hash-model-file",
            ]
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        elapsed = round(time.time() - t0, 2)

        # 复测判定：逐步响应合规性 + 触顶空输出
        n_steps = n_ok_fmt = n_trunc_empty = 0
        per_step = ep_out / "runner_out" / "per_step.csv"
        # baseline 目录名：v12 用 V12_ARMS 映射名；p1 用 baseline 名本身
        base_dir = {"vam_coder_v1.2_E": "vam_coder_v1.2_E", "vam_coder_v1.2_F": "vam_coder_v1.2_F",
                    "vam_coder_v1.3_V13A": "vam_coder_v1.3_V13A",
                    "vam_coder_v1.3_V13B": "vam_coder_v1.3_V13B",
                    "vam_coder_v1.2_H": "vam_coder_v1.2_H"}.get(arch, arch)
        # ablate 变体的 runner 目录名 = V12_ARMS[arm]（不带 ablate 后缀）
        if arch.startswith("vam_coder_v1.2_F_ablate"):
            base_dir = "vam_coder_v1.2_F"
        if arch.startswith("vam_coder_v1.2_E_ablate"):
            base_dir = "vam_coder_v1.2_E"
        step_root = ep_out / "runner_out" / "episodes" / task / base_dir / "steps"
        for sd in sorted(step_root.glob("step*")):
            n_steps += 1
            txt_p = sd / "response.txt"
            txt = txt_p.read_text(encoding="utf-8") if txt_p.exists() else ""
            rj = sd / "result.json"
            ct = 0
            if rj.exists():
                ct = int(json.loads(rj.read_text(encoding="utf-8")).get("completion_tokens") or 0)
            if "FILE:" in txt or "NO_EDIT" in txt:
                n_ok_fmt += 1
            if ct >= args.max_tokens and not txt.strip():
                n_trunc_empty += 1
        resolved = (proc.returncode == 0 and n_steps > 0
                    and n_trunc_empty == 0 and n_ok_fmt == n_steps)
        rec = {
            "episode_id": ep_id, "round": round_name, "task_id": task,
            "architecture": arch, "rep": rep, "status": "OK" if proc.returncode == 0 else f"RC_{proc.returncode}",
            "before_classes": ";".join(sorted(set(meta["before_classes"]))),
            "max_tokens": args.max_tokens,
            "n_steps": n_steps, "steps_format_ok": n_ok_fmt,
            "steps_trunc_empty": n_trunc_empty, "resolved": int(resolved),
            "elapsed_s": elapsed, "ts": now(),
        }
        if proc.returncode != 0:
            rec["stderr_tail"] = (proc.stderr or "")[-800:]
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        results.append(rec)
        n_new += 1
        print(f"[{n_new}] {ep_id} -> {rec['status']} steps={n_steps} fmt_ok={n_ok_fmt} "
              f"trunc_empty={n_trunc_empty} resolved={resolved} t={elapsed}s", flush=True)
        time.sleep(0.5)

    # 汇总（含续跑历史）
    all_recs = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                all_recs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    n = len(all_recs)
    n_res = sum(int(r.get("resolved") or 0) for r in all_recs)
    summary = {
        "schema": "protocol-retest-4096-v1",
        "purpose": "归因（protocol_attribution：51/51=EMPTY_TRUNC）后的受控复测；验证提高输出预算是否消除该类违规",
        "max_tokens": args.max_tokens,
        "episodes": n, "resolved": n_res,
        "resolved_rate": round(n_res / n, 4) if n else 0.0,
        "by_round": dict(Counter(r["round"] for r in all_recs)),
        "remaining_trunc_empty": sum(int(r.get("steps_trunc_empty") or 0) for r in all_recs),
        "note": "隔离目录重跑；不修改任何冻结实验数据；同温度/seed/任务清单，仅 max_tokens 变化",
        "finished_at": now(),
    }
    (out_root / "retest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = ["episode_id", "round", "task_id", "architecture", "rep", "status",
              "before_classes", "max_tokens", "n_steps", "steps_format_ok",
              "steps_trunc_empty", "resolved", "elapsed_s", "ts"]
    with (out_root / "retest_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_recs)
    print("SUMMARY", json.dumps({k: summary[k] for k in
          ("episodes", "resolved", "resolved_rate", "remaining_trunc_empty")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
