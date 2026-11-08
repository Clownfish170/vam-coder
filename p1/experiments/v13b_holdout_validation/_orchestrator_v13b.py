#!/usr/bin/env python
"""V1.3-B Holdout Round 2 orchestrator。

架构（完整标识，结果文件中一律使用全名，不缩写、不翻译）：
  - vam_coder_v1.2_E        （V12 digest 臂）
  - vam_coder_v1.2_F        （V12 full 臂）
  - vam_coder_v1.3_V13B     （V13B：F 默认 + 无实现体→NONE + 头部等长 [ctx]）
  - memory_off              （非 VAM：无记忆，全仓库源码）
  - symbol_full_read        （非 VAM：索引符号全量重读）

规模：12 tasks × 5 architectures × R=2 = 120 episodes（≤240 requests）。
随机化 seed = 20261104（round2 新顺序；bootstrap seed 仍为 20261102）。
任务集：与 round1 相同的冻结 holdout（manifest 哈希复核，内容零改动）。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parents[1]
ROOT = P1.parent
sys.path.insert(0, str(P1 / "scripts"))
sys.path.insert(0, str(HERE.parent / "v13_holdout_validation"))

import _orchestrator_v13 as r1  # noqa: E402  （复用冻结哈希核验）
from v12.workspace_audit import (  # noqa: E402
    write_episode_workspace_evidence,
    write_post_and_diff,
)

TASKS_DIR = P1 / "tasks_v13_holdout"
TASKS_JSON = TASKS_DIR / "holdout_tasks.json"

RANDOMIZATION_SEED = 20261104   # round2 专属（仅 episode 顺序）
BOOTSTRAP_SEED = 20261102       # 不变（prereg 冻结）
REPS = [1, 2]

# 架构注册表：全名 = 结果中的标注；runner 决定分派
ARCHITECTURES = [
    {"arch": "vam_coder_v1.2_E", "runner": "v12", "arm": "E", "baseline_dir": "vam_coder_v1.2_E"},
    {"arch": "vam_coder_v1.2_F", "runner": "v12", "arm": "F", "baseline_dir": "vam_coder_v1.2_F"},
    {"arch": "vam_coder_v1.3_V13B", "runner": "v12", "arm": "V13B", "baseline_dir": "vam_coder_v1.3_V13B"},
    {"arch": "memory_off", "runner": "p1", "baseline": "memory_off", "baseline_dir": "memory_off"},
    {"arch": "symbol_full_read", "runner": "p1", "baseline": "symbol_full_read", "baseline_dir": "symbol_full_read"},
]

CODE_SNAPSHOT_FILES = [
    "scripts/p1_common.py",
    "scripts/v12/levels.py",
    "scripts/v12/config.py",
    "scripts/v12/assemble.py",
    "scripts/v12/adaptive_features.py",
    "scripts/run_p1_v12.py",
    "scripts/run_p1.py",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_episodes(task_ids: list[str]) -> list[dict]:
    return [
        {"episode_id": f"{t}_{a['arch']}_R{r}", "task_id": t, "arch": a["arch"], "repetition": r, "spec": a}
        for t in task_ids
        for a in ARCHITECTURES
        for r in REPS
    ]


def read_step_rows(runner_out: Path) -> list[dict]:
    per_step = runner_out / "per_step.csv"
    if not per_step.exists():
        return []
    with per_step.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stop_check(rows: list[dict], cumulative_tokens: int, s5_limit: int) -> tuple[str, str]:
    for r in rows:
        try:
            ins = int(r.get("insufficient") or 0)
            toks = int(r.get("prompt_tokens") or 0) + int(r.get("completion_tokens") or 0)
        except (TypeError, ValueError):
            ins, toks = 0, 0
        if ins == 1 and toks > 0:
            return "S1", f"request despite INSUFFICIENT: {r.get('episode')}/{r.get('step')}"
        err = (r.get("error") or "").lower()
        if "connection refused" in err or "cannot connect" in err:
            return "S2", f"server refused: {r.get('episode')}/{r.get('step')}"
    if cumulative_tokens > s5_limit:
        return "S5", f"cumulative tokens {cumulative_tokens} > {s5_limit}"
    return "", ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="qwen2.5-coder-1.5b")
    ap.add_argument("--out", default=str(P1 / "experiments" / "v13b_holdout_validation"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--s5-limit", type=int, default=0, help="P+C 累计停机阈值；0=不设（dry-run 用）")
    args = ap.parse_args(argv)

    # 冻结核验：round1 同源（p1_common/提示哈希 + holdout manifest 逐文件）
    problems = r1.verify_frozen_hashes() + r1.verify_holdout()
    if problems:
        print("FROZEN CHECK FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 3

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    if (out_root / "execution_log.jsonl").exists():
        print(f"refusing: {out_root/'execution_log.jsonl'} exists", file=sys.stderr)
        return 2

    tasks_doc = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    task_ids = [e["id"] for e in tasks_doc["episodes"]]
    assert len(task_ids) == 12

    episodes = build_episodes(task_ids)
    assert len(episodes) == 120, len(episodes)

    rng = random.Random(RANDOMIZATION_SEED)
    order = list(episodes)
    rng.shuffle(order)
    (out_root / "randomization_manifest.json").write_text(
        json.dumps(
            {
                "schema": "v13b-randomization-v1",
                "random_seed": RANDOMIZATION_SEED,
                "randomization_method": "python random.Random(seed).shuffle",
                "scope": "episode execution order only",
                "episode_count": len(episodes),
                "original_episode_order": [e["episode_id"] for e in episodes],
                "randomized_episode_order": [e["episode_id"] for e in order],
                "architectures": [a["arch"] for a in ARCHITECTURES],
                "repetitions": REPS,
                "tasks": 12,
            },
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    run_meta = {
        "schema": "v13b-holdout-run-meta-v1",
        "created_at": now(),
        "round": "round2_v13b",
        "dry_run": args.dry_run,
        "architectures": [a["arch"] for a in ARCHITECTURES],
        "v13b_rule": (
            "related non-target: FULL if has_implementation_body "
            "(or uncomputable→conservative FULL), NONE if ast_no_def; "
            "unrelated→NONE; ET/C/must unchanged; context header normalized to '[ctx]' "
            "for all v12-runner architectures (equal-length measurement fix)"
        ),
        "plan": {
            "path": "p1/experiments/v12_p1_execution/v13_design/v13_m2_validation_plan_rev3.md",
            "sha256": r1.REV3_SHA256,
            "note": "round2 在 rev3 基础上的预声明变更：新增 V13B 臂、头部等长化、随机化 seed=20261104；任务集/统计口径/bootstrap seed 不变",
        },
        "frozen_hashes": {
            "system_prompt_sha256": r1._sha_text(r1.SYSTEM_PROMPT),
            "build_messages_source_sha256": r1._sha_text(
                __import__("inspect").getsource(r1.build_messages)
            ),
            "p1_common_sha256": r1._sha_bytes(Path(r1._p1c.__file__).read_bytes()),
        },
        "code_snapshot_sha256": {f: _sha(P1 / f) for f in CODE_SNAPSHOT_FILES},
        "holdout": {
            "tasks_json_sha256": _sha(TASKS_JSON),
            "manifest_sha256": _sha(TASKS_DIR / "holdout_manifest.json"),
        },
        "repetitions": REPS,
        "episodes_planned": 120,
        "requests_planned_max": 240,
        "randomization_seed": RANDOMIZATION_SEED,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_B": 10000,
        "stat_cluster": "task_id",
        "s5_token_limit": args.s5_limit,
        "model_requested": args.model,
        "context_window": 8192,
        "parallel": 1,
        "temperature": 0.0,
        "seed": 0,
        "max_tokens": 1024,
        "history_policy": "keep",
        "endpoint": args.endpoint,
        "python": sys.executable,
        "tasks_json": str(TASKS_JSON),
    }
    (out_root / "run_meta.json").write_text(
        json.dumps(run_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    logs = out_root / "episode_logs"
    logs.mkdir(exist_ok=True)
    log_path = out_root / "execution_log.jsonl"
    limit = args.limit if args.limit > 0 else len(order)

    cumulative_tokens = 0
    n_requests = 0
    ok = fail = 0
    stop_code = stop_reason = ""

    for i, ep in enumerate(order[:limit], 1):
        ep_id, task, arch, rep = ep["episode_id"], ep["task_id"], ep["arch"], ep["repetition"]
        spec = ep["spec"]
        ep_dir = logs / ep_id
        ep_dir.mkdir(parents=True, exist_ok=True)
        source = TASKS_DIR / task / "project"
        write_episode_workspace_evidence(
            source_project=source,
            workspace=ep_dir / "workspace_pending",
            episode_dir=ep_dir,
            episode_id=ep_id,
            task_id=task,
            arm=arch,
            repetition=rep,
        )
        runner_out = ep_dir / "runner_out"
        if spec["runner"] == "v12":
            cmd = [
                sys.executable, str(P1 / "scripts" / "run_p1_v12.py"),
                "--episode", task, "--arm", spec["arm"], "--rep", str(rep),
                "--tasks-json", str(TASKS_JSON), "--out-root", str(runner_out),
                "--pause-seconds", "0", "--closure-depth", "2",
                "--endpoint", args.endpoint, "--model", args.model,
                "--temperature", "0", "--seed", "0", "--max-tokens", "1024",
            ]
        else:
            cmd = [
                sys.executable, str(P1 / "scripts" / "run_p1.py"),
                "--tasks", str(TASKS_JSON),
                "--episode", task, "--baselines", spec["baseline"],
                "--rep", str(rep), "--out", str(runner_out),
                "--pause-seconds", "0",
                "--endpoint", args.endpoint, "--model", args.model,
                "--temperature", "0", "--seed", "0", "--max-tokens", "1024",
                "--history-policy", "keep",
                "--allow-manifest-mismatch", "--no-hash-model-file",
            ]
        if args.dry_run:
            cmd.append("--dry-run")

        t0 = time.time()
        proc = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace",  # Windows 控制台默认 GBK 会炸
        )
        elapsed = round(time.time() - t0, 2)

        rows = read_step_rows(runner_out)
        ep_tokens = 0
        ep_requests = 0
        for r in rows:
            try:
                pt = int(r.get("prompt_tokens") or 0)
                ct = int(r.get("completion_tokens") or 0)
            except (TypeError, ValueError):
                pt = ct = 0
            ep_tokens += pt + ct
            us = r.get("usage_source") or "none"
            if us != "none" or pt > 0 or ct > 0:
                ep_requests += 1
        cumulative_tokens += ep_tokens
        n_requests += ep_requests

        status = "OK" if proc.returncode == 0 else f"RC_{proc.returncode}"
        if proc.returncode == 0:
            ok += 1
        else:
            fail += 1
        try:
            write_post_and_diff(
                workspace=runner_out / "episodes" / task / spec["baseline_dir"] / "workspace",
                episode_dir=ep_dir,
                episode_id=ep_id,
                task_id=task,
                arm=arch,
                repetition=rep,
            )
        except Exception as e:  # noqa: BLE001
            status += "+POST_FAIL"
            print(f"  post evidence fail {ep_id}: {e!r}", flush=True)

        rec = {
            "episode_id": ep_id, "task_id": task, "architecture": arch,
            "repetition": rep, "order_index": i, "status": status,
            "rc": proc.returncode, "elapsed_s": elapsed, "steps": len(rows),
            "requests": ep_requests, "tokens": ep_tokens, "ts": now(),
        }
        if proc.returncode != 0:
            rec["stderr_tail"] = (proc.stderr or "")[-1200:]
            rec["stdout_tail"] = (proc.stdout or "")[-800:]
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(
            f"[{i}/{limit}] {ep_id} -> {status} steps={len(rows)} req={ep_requests} "
            f"tok={ep_tokens} cum={cumulative_tokens} t={elapsed}s",
            flush=True,
        )

        sc, sr = stop_check(rows, cumulative_tokens, args.s5_limit)
        if sc:
            stop_code, stop_reason = sc, sr
            print(f"STOP {sc}: {sr}", flush=True)
            break

    summary = {
        "finished_at": now(),
        "planned": 120,
        "attempted": sum(1 for _ in log_path.read_text(encoding="utf-8").splitlines()),
        "ok": ok, "fail": fail,
        "requests_made": n_requests,
        "cumulative_tokens": cumulative_tokens,
        "s5_token_limit": args.s5_limit,
        "randomization_seed": RANDOMIZATION_SEED,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "dry_run": args.dry_run,
        "stop_code": stop_code, "stop_reason": stop_reason,
    }
    (out_root / "execution_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))
    return 0 if not stop_code else 4


if __name__ == "__main__":
    raise SystemExit(main())
