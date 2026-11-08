#!/usr/bin/env python
"""Phase C: execute P0 smoke in frozen randomization order. No code changes to r2.2 core."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

P1 = Path(__file__).resolve().parents[3]  # .../p1
sys.path.insert(0, str(P1 / "scripts"))
sys.path.insert(0, str(P1.parent / "src"))

import run_p1_v12 as rp  # noqa: E402
from vam_coder.config import AppConfig  # noqa: E402

EXEC = P1 / "experiments" / "v12_p0_smoke" / "execution"
ORDER = EXEC / "execution_order.json"
ORDER.mkdir(parents=True, exist_ok=True)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    root = P1 / "experiments" / "v12_p0_smoke"
    rm = json.loads((root / "randomization_manifest.json").read_text(encoding="utf-8"))
    em = json.loads((root / "episode_manifest.json").read_text(encoding="utf-8"))
    by_id = {e["episode_id"]: e for e in em["episodes"]}
    order = rm["randomized_episode_order"]
    assert len(order) == 32

    cfg = AppConfig.load(P1.parent / "config" / "default.json")
    args = type("A", (), {})()
    args.dry_run = False
    args.pause_seconds = 1.0
    args.max_history_chars = 24000
    args.temperature = 0.0
    args.seed = 0
    args.max_tokens = 1024
    args.timeout = 300.0
    args.eval_timeout = 60.0
    args.mode_banner = "short"
    args.closure_depth = 2
    args.budget_tokens = 4096
    args.context_window = 8192

    out_root = EXEC / "runs"
    out_root.mkdir(parents=True, exist_ok=True)
    order_log = []
    model_calls = 0
    blocked = 0
    started = 0
    completed = 0

    # Load tasks
    meta = json.loads((P1 / "tasks" / "tasks_v1.0.json").read_text(encoding="utf-8"))
    by_task = {e["id"]: e for e in meta["episodes"]}

    for ep_id in order:
        meta_e = by_id[ep_id]
        task = meta_e["task_id"]
        arm = meta_e["arm"]
        rec = {
            "episode_id": ep_id,
            "task_id": task,
            "arm": arm,
            "started_at": now(),
            "status": "RUNNING",
        }
        order_log.append(rec)
        (ORDER / "log.json").write_text(
            json.dumps(order_log, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[start] {ep_id}", flush=True)
        started += 1
        try:
            rows = rp.run_episode_arm(
                episode=by_task[task],
                arm=arm,
                out_dir=out_root,
                model="qwen2.5-coder-1.5b",
                endpoint="http://127.0.0.1:8080/v1",
                args=args,
                cfg=cfg,
                rep=1,
            )
            if isinstance(rows, tuple):
                rows = rows[0]
            n_req = sum(
                1
                for r in rows
                if not str(r.get("error") or "").startswith(("dry_run", "INSUFFICIENT"))
                and (r.get("prompt_tokens") or 0) > 0
            )
            n_block = sum(
                1 for r in rows if "INSUFFICIENT" in str(r.get("error") or "")
            )
            model_calls += n_req
            blocked += n_block
            completed += 1
            rec["status"] = "COMPLETED"
            rec["model_requests"] = n_req
            rec["blocked_steps"] = n_block
            rec["finished_at"] = now()
        except Exception as e:
            rec["status"] = "ERROR"
            rec["error"] = repr(e)
            rec["finished_at"] = now()
            print(f"[STOP] {ep_id} {e!r}", flush=True)
            (ORDER / "log.json").write_text(
                json.dumps(order_log, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return 2
        (ORDER / "log.json").write_text(
            json.dumps(order_log, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        time.sleep(args.pause_seconds)

    summary = {
        "planned": 32,
        "started": started,
        "completed": completed,
        "model_requests": model_calls,
        "blocked_steps": blocked,
        "finished_at": now(),
        "seed": rm["random_seed"],
    }
    (ORDER / "actual_run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("[done]", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
