#!/usr/bin/env python
"""P1 orchestrator: 24 tasks × 7 arms × R=3 in frozen random order.

Workspace pre/post/diff per episode. Uses existing runners via subprocess.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

P1 = Path(__file__).resolve().parents[2]  # .../p1
ROOT = P1.parent
sys.path.insert(0, str(P1 / "scripts"))

from v12.workspace_audit import (  # noqa: E402
    build_workspace_manifest,
    workspace_diff,
    write_episode_workspace_evidence,
    write_post_and_diff,
)

ARMS = ["A", "B", "D", "E", "F", "G", "H"]
SEED = 20261102


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_tasks() -> list[dict]:
    meta = json.loads((P1 / "tasks" / "tasks_v1.0.json").read_text(encoding="utf-8"))
    return meta["episodes"]


def make_order(tasks: list[str], arms: list[str], rep: int) -> list[dict]:
    original = [
        {"episode_id": f"{t}_{a}_R{rep}", "task_id": t, "arm": a, "repetition": rep}
        for t in tasks
        for a in arms
        for rep in [rep]
    ]
    # fix: rep is loop variable in comprehension incorrectly - rebuild properly
    return original


def build_episodes(task_ids: list[str]) -> list[dict]:
    eps = []
    for t in task_ids:
        for a in ARMS:
            for r in (1, 2, 3):
                eps.append(
                    {
                        "episode_id": f"{t}_{a}_R{r}",
                        "task_id": t,
                        "arm": a,
                        "repetition": r,
                    }
                )
    return eps


def find_workspace(run_dir: Path, task: str, arm: str) -> Path | None:
    """Locate workspace under a runner output directory."""
    if arm in ("E", "F", "G", "H"):
        p = run_dir / "episodes" / task / f"vam_coder_v1.2_{arm}" / "workspace"
        if p.exists():
            return p
    if arm == "D":
        p = run_dir / "episodes" / task / "vam_coder_v1.1" / "workspace"
        if p.exists():
            return p
    if arm == "A":
        p = run_dir / "episodes" / task / "memory_off" / "workspace"
        if p.exists():
            return p
    if arm == "B":
        p = run_dir / "episodes" / task / "symbol_full_read" / "workspace"
        if p.exists():
            return p
    # fallback search
    hits = list(run_dir.glob(f"episodes/{task}/*/workspace"))
    return hits[0] if hits else None


def run_arm(task: str, arm: str, rep: int, out_dir: Path, args) -> int:
    py = sys.executable
    out_dir.mkdir(parents=True, exist_ok=True)
    if arm in ("E", "F", "G", "H"):
        cmd = [
            py,
            str(P1 / "scripts" / "run_p1_v12.py"),
            "--episode",
            task,
            "--arm",
            arm,
            "--rep",
            str(rep),
            "--out-root",
            str(out_dir),
            "--pause-seconds",
            "0",
            "--closure-depth",
            "2",
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        if not args.dry_run:
            cmd += [
                "--endpoint",
                args.endpoint,
                "--model",
                args.model,
                "--temperature",
                "0",
                "--seed",
                "0",
                "--max-tokens",
                "1024",
            ]
    elif arm == "D":
        cmd = [
            py,
            str(P1 / "scripts" / "run_p1_v11.py"),
            "--episode",
            task,
            "--baselines",
            "vam_coder_v1.1",
            "--rep",
            str(rep),
            "--out-root",
            str(out_dir),
            "--pause-seconds",
            "0",
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        else:
            cmd += ["--endpoint", args.endpoint, "--model", args.model]
    elif arm == "A":
        baseline = "memory_off"
        cmd = [
            py,
            str(P1 / "scripts" / "run_p1.py"),
            "--tasks",
            str(P1 / "tasks" / "tasks_v1.0.json"),
            "--episode",
            task,
            "--baselines",
            baseline,
            "--rep",
            str(rep),
            "--out",
            str(out_dir),
            "--pause-seconds",
            "0",
            "--allow-manifest-mismatch",
            "--no-hash-model-file",
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        else:
            cmd += ["--endpoint", args.endpoint, "--model", args.model]
    elif arm == "B":
        baseline = "symbol_full_read"
        cmd = [
            py,
            str(P1 / "scripts" / "run_p1.py"),
            "--tasks",
            str(P1 / "tasks" / "tasks_v1.0.json"),
            "--episode",
            task,
            "--baselines",
            baseline,
            "--rep",
            str(rep),
            "--out",
            str(out_dir),
            "--pause-seconds",
            "0",
            "--allow-manifest-mismatch",
            "--no-hash-model-file",
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        else:
            cmd += ["--endpoint", args.endpoint, "--model", args.model]
    else:
        raise ValueError(arm)

    print(f"  exec {arm} {task} R{rep}", flush=True)
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout[-2000:] if proc.stdout else "", flush=True)
        print(proc.stderr[-2000:] if proc.stderr else "", flush=True)
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="qwen2.5-coder-1.5b")
    ap.add_argument("--limit", type=int, default=0, help="0=all; else first N episodes")
    ap.add_argument("--out", default=str(P1 / "experiments" / "v12_p1_execution"))
    args = ap.parse_args()

    out_root = Path(args.out)
    runs = out_root / "runs"
    runs.mkdir(parents=True, exist_ok=True)

    tasks = [e["id"] for e in load_tasks()]
    assert len(tasks) == 24
    episodes = build_episodes(tasks)
    assert len(episodes) == 504, len(episodes)

    rng = random.Random(SEED)
    order = list(episodes)
    rng.shuffle(order)
    ids = [e["episode_id"] for e in order]
    assert len(set(ids)) == 504

    # freeze randomization
    rand_path = out_root / "randomization_manifest.json"
    if rand_path.exists() and not args.dry_run:
        existing = json.loads(rand_path.read_text(encoding="utf-8"))
        if existing.get("random_seed") != SEED or existing.get("episode_count") != 504:
            print("randomization mismatch", file=sys.stderr)
            return 2
        order_ids = existing["randomized_episode_order"]
        by = {e["episode_id"]: e for e in episodes}
        order = [by[i] for i in order_ids]
    else:
        rand_path.write_text(
            json.dumps(
                {
                    "schema": "v12-p1-randomization-v1",
                    "random_seed": SEED,
                    "randomization_method": "python random.Random(seed).shuffle",
                    "original_episode_order": [e["episode_id"] for e in episodes],
                    "randomized_episode_order": ids,
                    "episode_count": 504,
                    "arms": ARMS,
                    "repetition": 3,
                    "tasks": 24,
                    "uniqueness_check": {"all_unique": True, "count": len(set(ids))},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    limit = args.limit if args.limit > 0 else len(order)
    log_path = out_root / "execution_log.jsonl"
    ok = 0
    fail = 0
    for i, ep in enumerate(order[:limit], 1):
        ep_id = ep["episode_id"]
        task, arm, rep = ep["task_id"], ep["arm"], ep["repetition"]
        ep_dir = runs / ep_id
        source = P1 / "tasks" / task / "project"
        # PRE manifest before any model call
        write_episode_workspace_evidence(
            source_project=source,
            workspace=ep_dir / "workspace_pending",
            episode_dir=ep_dir,
            episode_id=ep_id,
            task_id=task,
            arm=arm,
            repetition=rep,
        )
        # runner out inside episode dir
        runner_out = ep_dir / "runner_out"
        t0 = time.time()
        rc = run_arm(task, arm, rep, runner_out, args)
        ws = find_workspace(runner_out, task, arm)
        if ws is None:
            print(f"  ERROR no workspace {ep_id}", flush=True)
            fail += 1
            rec = {"episode_id": ep_id, "status": "NO_WORKSPACE", "rc": rc, "ts": now()}
        else:
            try:
                write_post_and_diff(
                    workspace=ws,
                    episode_dir=ep_dir,
                    episode_id=ep_id,
                    task_id=task,
                    arm=arm,
                    repetition=rep,
                )
                rec = {
                    "episode_id": ep_id,
                    "status": "OK" if rc == 0 else f"RC_{rc}",
                    "rc": rc,
                    "elapsed_s": round(time.time() - t0, 2),
                    "ts": now(),
                }
                if rc == 0:
                    ok += 1
                else:
                    fail += 1
            except Exception as e:
                rec = {"episode_id": ep_id, "status": "POST_FAIL", "err": repr(e), "ts": now()}
                fail += 1
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[{i}/{limit}] {ep_id} -> {rec['status']}", flush=True)
        if not args.dry_run:
            time.sleep(0.3)

    summary = {
        "finished_at": now(),
        "planned": 504,
        "attempted": min(limit, 504),
        "ok": ok,
        "fail": fail,
        "seed": SEED,
        "dry_run": args.dry_run,
    }
    (out_root / "execution_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SUMMARY", summary)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
