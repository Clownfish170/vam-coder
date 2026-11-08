#!/usr/bin/env python
"""P1 确认性实验 orchestrator（预注册 v1 §5）。

架构（完整标识）：vam_coder_v1.2_F / memory_off / symbol_full_read
规模：48 tasks × 3 architectures × R=5 = 720 episodes（4080 requests）
冻结：prereg sha=088898a3aec9d08411864ea03ff79ac7ff3e78411ed34a58de89ecd0881cc7ed
      p1_tasks sha=d44445b2b8bff0a4338e8694194384235f73d0ea20b3d9550ae5d297c6f8f33b
      max_tokens=2048；随机化 seed=20261107；bootstrap seed=20261102
续跑：execution_log.jsonl 中已 OK 的 episode 自动跳过；累计 token 结入 S5。
S5 = 6,600,000（2× dry-run 预估 3.3M）。
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

import p1_common as _p1c  # noqa: E402
from p1_common import SYSTEM_PROMPT, build_messages  # noqa: E402
from v12.workspace_audit import write_episode_workspace_evidence, write_post_and_diff  # noqa: E402

TASKS_DIR = P1 / "tasks_p1_validation"
TASKS_JSON = TASKS_DIR / "p1_tasks.json"
TASKS_MANIFEST = TASKS_DIR / "p1_tasks_manifest.json"
PREREG = P1 / "docs" / "v12f_validation_preregistration.md"

PREREG_SHA256 = "088898a3aec9d08411864ea03ff79ac7ff3e78411ed34a58de89ecd0881cc7ed"
P1_TASKS_SHA256 = "d44445b2b8bff0a4338e9694194384235f73d0ea20b3d9550ae5d297c6f8f33b"
P1_COMMON_SHA256 = "b6ce07a3bccbcb20fe94e8346fff0b7d8f55b6dea5fc0356da3b15c26e88a9b6"
SYS_PROMPT_SHA256 = "4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a"
BUILD_MSG_SHA256 = "f0b477b0046282739ba1309e5035b2beb2f2f8d2564535d7154019a9aee9e436"

RANDOMIZATION_SEED = 20261107
BOOTSTRAP_SEED = 20261102
REPS = [1, 2, 3, 4, 5]
S5_LIMIT = 6_600_000

ARCHITECTURES = [
    {"arch": "vam_coder_v1.2_F", "runner": "v12", "arm": "F", "baseline_dir": "vam_coder_v1.2_F"},
    {"arch": "memory_off", "runner": "p1", "baseline": "memory_off", "baseline_dir": "memory_off"},
    {"arch": "symbol_full_read", "runner": "p1", "baseline": "symbol_full_read", "baseline_dir": "symbol_full_read"},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_frozen() -> list[str]:
    import inspect
    problems = []
    if _sha(PREREG) != PREREG_SHA256:
        problems.append("preregistration sha mismatch")
    if _sha(TASKS_JSON) != P1_TASKS_SHA256:
        problems.append("p1_tasks.json sha mismatch")
    if _sha_text(SYSTEM_PROMPT) != SYS_PROMPT_SHA256:
        problems.append("SYSTEM_PROMPT sha mismatch")
    if _sha_text(inspect.getsource(build_messages)) != BUILD_MSG_SHA256:
        problems.append("build_messages sha mismatch")
    if _sha(Path(_p1c.__file__)) != P1_COMMON_SHA256:
        problems.append("p1_common sha mismatch")
    # manifest 指向的 tasks sha
    mf = json.loads(TASKS_MANIFEST.read_text(encoding="utf-8"))
    if mf.get("p1_tasks_sha256") != P1_TASKS_SHA256:
        problems.append("manifest.tasks_sha mismatch")
    return problems


def _sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def build_episodes(task_ids: list[str]) -> list[dict]:
    return [
        {"episode_id": f"{t}_{a['arch']}_R{r}", "task_id": t, "arch": a["arch"],
         "repetition": r, "spec": a}
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


def stop_check(rows: list[dict], cumulative: int) -> tuple[str, str]:
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
    if cumulative > S5_LIMIT:
        return "S5", f"cumulative tokens {cumulative} > {S5_LIMIT}"
    return "", ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="https://maas.qianwenaiapi.com/compatible-mode/v1")
    ap.add_argument("--model", default="deepseek-v4.1-flash-1017")
    ap.add_argument("--out", default=str(P1 / "experiments" / "p1_validation"))
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--limit", type=int, default=0, help="本轮最多执行的新 episode 数（0=全部，续跑用）")
    args = ap.parse_args(argv)

    problems = verify_frozen()
    if problems:
        print("FROZEN CHECK FAILED:", file=sys.stderr)
        for x in problems:
            print(" -", x, file=sys.stderr)
        return 3

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    log_path = out_root / "execution_log.jsonl"

    # 续跑：已完成（OK）的 episode 跳过；历史 token 计入累计
    done: set[str] = set()
    prior_tokens = 0
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("status") == "OK":
                done.add(rec["episode_id"])
            prior_tokens += int(rec.get("tokens") or 0)
    print(f"[resume] done={len(done)} prior_tokens={prior_tokens}")

    tasks_doc = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    task_ids = [e["id"] for e in tasks_doc["episodes"]]
    assert len(task_ids) == 48
    episodes = build_episodes(task_ids)
    assert len(episodes) == 720, len(episodes)

    rng = random.Random(RANDOMIZATION_SEED)
    order = list(episodes)
    rng.shuffle(order)
    rand_path = out_root / "randomization_manifest.json"
    if rand_path.exists():
        existing = json.loads(rand_path.read_text(encoding="utf-8"))
        assert existing.get("random_seed") == RANDOMIZATION_SEED
        by = {e["episode_id"]: e for e in episodes}
        order = [by[i] for i in existing["randomized_episode_order"]]
    else:
        rand_path.write_text(json.dumps({
            "schema": "p1-randomization-v1",
            "random_seed": RANDOMIZATION_SEED,
            "randomization_method": "python random.Random(seed).shuffle",
            "scope": "episode execution order only",
            "episode_count": 720,
            "original_episode_order": [e["episode_id"] for e in episodes],
            "randomized_episode_order": [e["episode_id"] for e in order],
            "architectures": [a["arch"] for a in ARCHITECTURES],
            "repetitions": REPS,
            "tasks": 48,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run_meta_path = out_root / "run_meta.json"
    if not run_meta_path.exists():
        run_meta_path.write_text(json.dumps({
            "schema": "p1-run-meta-v1",
            "created_at": now(),
            "round": "p1_confirmatory",
            "prereg": {"path": "p1/docs/v12f_validation_preregistration.md",
                       "sha256": PREREG_SHA256},
            "task_set": {"path": str(TASKS_JSON), "sha256": P1_TASKS_SHA256,
                         "manifest_sha256": _sha(TASKS_MANIFEST)},
            "architectures": [a["arch"] for a in ARCHITECTURES],
            "repetitions": REPS,
            "episodes_planned": 720,
            "requests_planned_max": 4080,
            "max_tokens": args.max_tokens,
            "s5_token_limit": S5_LIMIT,
            "s5_basis": "2× dry-run estimate 3.3M (validation_p0)",
            "randomization_seed": RANDOMIZATION_SEED,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_B": 10000,
            "frozen_hashes": {
                "system_prompt_sha256": _sha_text(SYSTEM_PROMPT),
                "build_messages_source_sha256": _sha_text(__import__("inspect").getsource(build_messages)),
                "p1_common_sha256": _sha(Path(_p1c.__file__)),
            },
            "model": args.model,
            "endpoint": args.endpoint,
            "temperature": 0.0,
            "seed": 0,
            "history_policy": "keep",
            "python": sys.executable,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    logs = out_root / "episode_logs"
    logs.mkdir(exist_ok=True)
    limit = args.limit if args.limit > 0 else len(order)

    cumulative = prior_tokens
    n_requests_new = 0
    executed_new = ok_new = fail_new = 0
    stop_code = stop_reason = ""

    for i, ep in enumerate(order, 1):
        if ep["episode_id"] in done:
            continue
        if executed_new >= limit:
            break
        ep_id, task, arch, rep = ep["episode_id"], ep["task_id"], ep["arch"], ep["repetition"]
        spec = ep["spec"]
        ep_dir = logs / ep_id
        ep_dir.mkdir(parents=True, exist_ok=True)
        source = TASKS_DIR / task / "project"
        write_episode_workspace_evidence(
            source_project=source, workspace=ep_dir / "workspace_pending",
            episode_dir=ep_dir, episode_id=ep_id, task_id=task,
            arm=arch, repetition=rep,
        )
        runner_out = ep_dir / "runner_out"
        if spec["runner"] == "v12":
            cmd = [
                sys.executable, str(P1 / "scripts" / "run_p1_v12.py"),
                "--episode", task, "--arm", spec["arm"], "--rep", str(rep),
                "--tasks-json", str(TASKS_JSON), "--out-root", str(runner_out),
                "--pause-seconds", "0", "--closure-depth", "2",
                "--endpoint", args.endpoint, "--model", args.model,
                "--temperature", "0", "--seed", "0",
                "--max-tokens", str(args.max_tokens),
            ]
        else:
            cmd = [
                sys.executable, str(P1 / "scripts" / "run_p1.py"),
                "--tasks", str(TASKS_JSON),
                "--episode", task, "--baselines", spec["baseline"],
                "--rep", str(rep), "--out", str(runner_out),
                "--pause-seconds", "0",
                "--endpoint", args.endpoint, "--model", args.model,
                "--temperature", "0", "--seed", "0",
                "--max-tokens", str(args.max_tokens),
                "--history-policy", "keep",
                "--allow-manifest-mismatch", "--no-hash-model-file",
            ]
        t0 = time.time()
        proc = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
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
            if (r.get("usage_source") or "none") != "none" or pt > 0 or ct > 0:
                ep_requests += 1
        cumulative += ep_tokens
        n_requests_new += ep_requests
        executed_new += 1

        status = "OK" if proc.returncode == 0 else f"RC_{proc.returncode}"
        if proc.returncode == 0:
            ok_new += 1
        else:
            fail_new += 1
        try:
            write_post_and_diff(
                workspace=runner_out / "episodes" / task / spec["baseline_dir"] / "workspace",
                episode_dir=ep_dir, episode_id=ep_id, task_id=task,
                arm=arch, repetition=rep,
            )
        except Exception as e:  # noqa: BLE001
            status += "+POST_FAIL"
            print(f"  post fail {ep_id}: {e!r}", flush=True)

        rec = {
            "episode_id": ep_id, "task_id": task, "architecture": arch,
            "repetition": rep, "order_index": i, "status": status,
            "rc": proc.returncode, "elapsed_s": elapsed, "steps": len(rows),
            "requests": ep_requests, "tokens": ep_tokens, "ts": now(),
        }
        if proc.returncode != 0:
            rec["stderr_tail"] = (proc.stderr or "")[-1200:]
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if executed_new % 10 == 0 or status != "OK":
            print(f"[{executed_new}/{limit}] {ep_id} -> {status} steps={len(rows)} "
                  f"tok={ep_tokens} cum={cumulative}", flush=True)

        sc, sr = stop_check(rows, cumulative)
        if sc:
            stop_code, stop_reason = sc, sr
            print(f"STOP {sc}: {sr}", flush=True)
            break
        time.sleep(0.5)

    summary = {
        "finished_at": now(), "planned": 720,
        "done_total": len(done) + ok_new,
        "executed_new": executed_new, "ok_new": ok_new, "fail_new": fail_new,
        "requests_new": n_requests_new,
        "cumulative_tokens": cumulative, "s5_limit": S5_LIMIT,
        "randomization_seed": RANDOMIZATION_SEED,
        "max_tokens": args.max_tokens,
        "stop_code": stop_code, "stop_reason": stop_reason,
        "resumed": bool(done),
    }
    (out_root / "execution_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))
    return 0 if not stop_code else 4


if __name__ == "__main__":
    raise SystemExit(main())
