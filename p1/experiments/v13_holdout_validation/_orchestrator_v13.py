#!/usr/bin/env python
"""V1.3-M2 Holdout orchestrator：12 tasks × E/F/V13A × R=2 = 72 episodes。

冻结依据：v13_m2_validation_plan_rev3.md（sha256 校验，不一致即停）。
- 随机化 seed=20261103（仅 episode 顺序）。
- Bootstrap seed=20261102 只写入元数据（分析阶段使用）。
- 无自动重试；失败保留记录；S1/S2/S5 触发即停并记录。
- S7 仅诊断不参与停止（本脚本不做 S7 判定）。

用法（仓库根 vam-coder/）：
  python p1/experiments/v13_holdout_validation/_orchestrator_v13.py --dry-run --out <dry_root>
  python p1/experiments/v13_holdout_validation/_orchestrator_v13.py --out p1/experiments/v13_holdout_validation
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parents[1]          # .../p1
ROOT = P1.parent               # .../vam-coder
sys.path.insert(0, str(P1 / "scripts"))

import p1_common as _p1c  # noqa: E402
from p1_common import SYSTEM_PROMPT, build_messages  # noqa: E402
from v12.workspace_audit import (  # noqa: E402
    write_episode_workspace_evidence,
    write_post_and_diff,
)

# ---------- rev3 冻结哈希 ----------
REV3_PATH = P1 / "experiments" / "v12_p1_execution" / "v13_design" / "v13_m2_validation_plan_rev3.md"
REV3_SHA256 = "8ceed45d6554ba952a641fbbebb49b4f3eb0f69858c16ba9d58d7025eb9ee13f"
SYS_PROMPT_SHA256 = "4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a"
P1_COMMON_SHA256 = "e32fd30517322e8976c8f7710be69fae508c9957a926079c526f9468a3f384f2"
BUILD_MESSAGES_SHA256 = "f0b477b0046282739ba1309e5035b2beb2f2f8d2564535d7154019a9aee9e436"

RANDOMIZATION_SEED = 20261103   # rev3 §3.3
BOOTSTRAP_SEED = 20261102       # rev3 §3.3 / prereg §7
BOOTSTRAP_B = 10000
ARMS = ["E", "F", "V13A"]
REPS = [1, 2]
TASKS_DIR = P1 / "tasks_v13_holdout"
TASKS_JSON = TASKS_DIR / "holdout_tasks.json"
MANIFEST_JSON = TASKS_DIR / "holdout_manifest.json"

# rev3 §5.1 预算（est）与 §5.2 S5 停机阈值
PLAN_TOKENS_EST = 42000
S5_TOKEN_LIMIT = 2 * PLAN_TOKENS_EST  # 84000

# 字符串 → sha256
def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha_text(s: str) -> str:
    return _sha_bytes(s.encode("utf-8"))


def _dir_fingerprints(d: Path) -> tuple[dict[str, str], str]:
    out: dict[str, str] = {}
    for p in sorted(d.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            out[p.relative_to(d).as_posix()] = _sha_bytes(p.read_bytes())
    agg = _sha_text("\n".join(f"{k}:{v}" for k, v in sorted(out.items())))
    return out, agg


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def verify_frozen_hashes() -> list[str]:
    """rev3 §3.1.1：三项 prompt 哈希 + rev3 自身；返回问题列表。"""
    problems: list[str] = []
    if _sha_bytes(REV3_PATH.read_bytes()) != REV3_SHA256:
        problems.append("rev3 sha256 mismatch")
    if _sha_bytes(Path(_p1c.__file__).read_bytes()) != P1_COMMON_SHA256:
        problems.append("p1_common.py sha256 mismatch")
    if _sha_text(SYSTEM_PROMPT) != SYS_PROMPT_SHA256:
        problems.append("SYSTEM_PROMPT sha256 mismatch")
    if _sha_text(inspect.getsource(build_messages)) != BUILD_MESSAGES_SHA256:
        problems.append("build_messages source sha256 mismatch")
    return problems


def verify_holdout() -> list[str]:
    """S3：holdout 冻结内容核验（任务清单 + 逐文件/指令/eval 哈希）。"""
    problems: list[str] = []
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    tasks_doc = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    if _sha_bytes(TASKS_JSON.read_bytes()) != manifest["holdout_tasks_sha256"]:
        problems.append("holdout_tasks.json sha mismatch vs manifest")
    by_id = {e["id"]: e for e in tasks_doc["episodes"]}
    for entry in manifest["tasks"]:
        tid = entry["id"]
        if tid not in by_id:
            problems.append(f"{tid}: missing in holdout_tasks.json")
            continue
        tdir = TASKS_DIR / tid
        # 项目文件
        fp, _ = _dir_fingerprints(tdir / "project")
        if fp != entry["project_files_sha256"]:
            problems.append(f"{tid}: project files hash mismatch")
        # 指令
        steps = by_id[tid]["steps"]
        for i, s in enumerate(steps, 1):
            if _sha_text(s["instruction"]) != entry["steps"][i - 1]["instruction_sha256"]:
                problems.append(f"{tid} step{i}: instruction hash mismatch")
            _, ev_agg = _dir_fingerprints(tdir / "eval" / f"step{i}")
            if ev_agg != entry["eval_sha256"][f"step{i}"]:
                problems.append(f"{tid} step{i}: eval hash mismatch")
    return problems


def build_episodes(task_ids: list[str]) -> list[dict]:
    return [
        {"episode_id": f"{t}_{a}_R{r}", "task_id": t, "arm": a, "repetition": r}
        for t in task_ids
        for a in ARMS
        for r in REPS
    ]


def read_step_rows(runner_out: Path) -> list[dict]:
    rows: list[dict] = []
    per_step = runner_out / "per_step.csv"
    if per_step.exists():
        with per_step.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    return rows


def stop_check(rec: dict, rows: list[dict], cumulative_tokens: int) -> tuple[str, str]:
    """返回 (stop_code, reason)；空串 = 继续。"""
    # S1：INSUFFICIENT 步仍发出请求（VP 违规仍请求的等价检测）
    for r in rows:
        try:
            ins = int(r.get("insufficient") or 0)
            toks = int(r.get("prompt_tokens") or 0) + int(r.get("completion_tokens") or 0)
        except ValueError:
            ins, toks = 0, 0
        if ins == 1 and toks > 0:
            return "S1", f"request sent despite INSUFFICIENT: {r.get('episode')}/{r.get('step')}"
    # S2：server 拒绝
    for r in rows:
        err = (r.get("error") or "").lower()
        if "connection refused" in err or "refused" in err or "cannot connect" in err:
            return "S2", f"server refused: {r.get('episode')}/{r.get('step')}: {r.get('error')}"
    # S5：token > 2× 计划
    if cumulative_tokens > S5_TOKEN_LIMIT:
        return "S5", f"cumulative tokens {cumulative_tokens} > {S5_TOKEN_LIMIT} (2× plan {PLAN_TOKENS_EST})"
    return "", ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="qwen2.5-coder-1.5b")
    ap.add_argument("--out", default=str(P1 / "experiments" / "v13_holdout_validation"))
    ap.add_argument("--limit", type=int, default=0, help="0=全部；否则前 N 个 episode（仅调试）")
    args = ap.parse_args(argv)

    # ---- 冻结核验（任一失败 → 停，S3/§3.1.1）
    problems = verify_frozen_hashes() + verify_holdout()
    if problems:
        print("FROZEN CHECK FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 3

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    if (out_root / "execution_log.jsonl").exists():
        print(f"refusing: {out_root/'execution_log.jsonl'} exists (no overwrite)", file=sys.stderr)
        return 2

    tasks_doc = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    task_ids = [e["id"] for e in tasks_doc["episodes"]]
    assert len(task_ids) == 12

    episodes = build_episodes(task_ids)
    assert len(episodes) == 72, len(episodes)

    # ---- 随机化（seed=20261103，仅顺序）
    rand_path = out_root / "randomization_manifest.json"
    rng = random.Random(RANDOMIZATION_SEED)
    order = list(episodes)
    rng.shuffle(order)
    rand_path.write_text(
        json.dumps(
            {
                "schema": "v13-randomization-v1",
                "random_seed": RANDOMIZATION_SEED,
                "randomization_method": "python random.Random(seed).shuffle",
                "scope": "episode execution order only",
                "episode_count": len(episodes),
                "original_episode_order": [e["episode_id"] for e in episodes],
                "randomized_episode_order": [e["episode_id"] for e in order],
                "arms": ARMS,
                "repetitions": REPS,
                "tasks": 12,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # ---- run_meta（rev3 §3.1.1 / §5.3）
    run_meta = {
        "schema": "v13-holdout-run-meta-v1",
        "created_at": now(),
        "dry_run": args.dry_run,
        "plan": {
            "path": "p1/experiments/v12_p1_execution/v13_design/v13_m2_validation_plan_rev3.md",
            "sha256": REV3_SHA256,
        },
        "frozen_hashes": {
            "system_prompt_sha256": _sha_text(SYSTEM_PROMPT),
            "build_messages_source_sha256": _sha_text(inspect.getsource(build_messages)),
            "p1_common_sha256": _sha_bytes(Path(_p1c.__file__).read_bytes()),
        },
        "holdout": {
            "tasks_json_sha256": _sha_bytes(TASKS_JSON.read_bytes()),
            "manifest_sha256": _sha_bytes(MANIFEST_JSON.read_bytes()),
        },
        "arms": ARMS,
        "repetitions": REPS,
        "episodes_planned": 72,
        "requests_planned_max": 144,
        "randomization_seed": RANDOMIZATION_SEED,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_B": BOOTSTRAP_B,
        "stat_cluster": "task_id",
        "plan_tokens_est": PLAN_TOKENS_EST,
        "s5_token_limit": S5_TOKEN_LIMIT,
        "model_requested": args.model,
        "model_actual": str(ROOT.parent / "models" / "qwen2.5-coder-1.5b-instruct-q6_k.gguf"),
        "model_quant": "Q6_K",
        "context_window": 8192,
        "parallel": 1,
        "temperature": 0.0,
        "seed": 0,
        "max_tokens": 1024,
        "history_policy": "keep",
        "closure_depth": 2,
        "k_max": 8,
        "endpoint": args.endpoint,
        "python": sys.executable,
        "tasks_json": str(TASKS_JSON),
    }
    (out_root / "run_meta.json").write_text(
        json.dumps(run_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    runs = out_root / "episode_logs"
    runs.mkdir(exist_ok=True)
    log_path = out_root / "execution_log.jsonl"
    limit = args.limit if args.limit > 0 else len(order)

    cumulative_tokens = 0
    n_requests = 0
    ok = fail = 0
    stop_code = stop_reason = ""

    for i, ep in enumerate(order[:limit], 1):
        ep_id, task, arm, rep = ep["episode_id"], ep["task_id"], ep["arm"], ep["repetition"]
        ep_dir = runs / ep_id
        ep_dir.mkdir(parents=True, exist_ok=True)
        source = TASKS_DIR / task / "project"
        write_episode_workspace_evidence(
            source_project=source,
            workspace=ep_dir / "workspace_pending",
            episode_dir=ep_dir,
            episode_id=ep_id,
            task_id=task,
            arm=arm,
            repetition=rep,
        )
        runner_out = ep_dir / "runner_out"
        cmd = [
            sys.executable,
            str(P1 / "scripts" / "run_p1_v12.py"),
            "--episode", task,
            "--arm", arm,
            "--rep", str(rep),
            "--tasks-json", str(TASKS_JSON),
            "--out-root", str(runner_out),
            "--pause-seconds", "0",
            "--closure-depth", "2",
            "--endpoint", args.endpoint,
            "--model", args.model,
            "--temperature", "0",
            "--seed", "0",
            "--max-tokens", "1024",
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        elapsed = round(time.time() - t0, 2)

        rows = read_step_rows(runner_out)
        ep_tokens = 0
        ep_requests = 0
        for r in rows:
            try:
                pt = int(r.get("prompt_tokens") or 0)
                ct = int(r.get("completion_tokens") or 0)
            except ValueError:
                pt = ct = 0
            ep_tokens += pt + ct
            us = r.get("usage_source") or "none"
            if us != "none" or pt > 0 or ct > 0:
                ep_requests += 1
        cumulative_tokens += ep_tokens
        n_requests += ep_requests

        status = "OK" if proc.returncode == 0 else f"RC_{proc.returncode}"
        if proc.returncode != 0:
            fail += 1
        else:
            # 有 eval 的行全空（runner 未跑完）也计 fail
            if rows and all((r.get("eval_success") or "") == "" for r in rows) and not args.dry_run:
                status = "NO_EVAL_ROWS"
                fail += 1
            else:
                ok += 1
        try:
            write_post_and_diff(
                workspace=runner_out / "episodes" / task / f"vam_coder_{'v1.2_' + arm if arm in ('E','F') else 'v1.3_V13A'}" / "workspace",
                episode_dir=ep_dir,
                episode_id=ep_id,
                task_id=task,
                arm=arm,
                repetition=rep,
            )
        except Exception as e:  # noqa: BLE001
            status = status + "+POST_FAIL"
            print(f"  post evidence fail {ep_id}: {e!r}", flush=True)

        rec = {
            "episode_id": ep_id,
            "task_id": task,
            "arm": arm,
            "repetition": rep,
            "order_index": i,
            "status": status,
            "rc": proc.returncode,
            "elapsed_s": elapsed,
            "steps": len(rows),
            "requests": ep_requests,
            "tokens": ep_tokens,
            "ts": now(),
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

        sc, sr = stop_check(rec, rows, cumulative_tokens)
        if sc:
            stop_code, stop_reason = sc, sr
            print(f"STOP {sc}: {sr}", flush=True)
            break

    summary = {
        "finished_at": now(),
        "planned": 72,
        "attempted": min(limit, 72) if not stop_code else sum(
            1 for _ in log_path.read_text(encoding="utf-8").splitlines()
        ),
        "ok": ok,
        "fail": fail,
        "requests_made": n_requests,
        "cumulative_tokens": cumulative_tokens,
        "s5_token_limit": S5_TOKEN_LIMIT,
        "randomization_seed": RANDOMIZATION_SEED,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "dry_run": args.dry_run,
        "stop_code": stop_code,
        "stop_reason": stop_reason,
    }
    (out_root / "execution_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))
    return 0 if not stop_code else 4


if __name__ == "__main__":
    raise SystemExit(main())
