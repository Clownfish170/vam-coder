#!/usr/bin/env python
"""双 Token 独立消融 orchestrator（补记冻结 d664d602…；确认性机制专项）。

臂（完整标识）：
  dualtoken_A_inline_full_context        （A：每轮原文内联重发 = F + --no-oprime）
  dualtoken_B_symbolic_addressing        （B：符号 ID 寻址 + 命中符号源码切片）
  dualtoken_C_static_rep_plus_symbolic_id（C：静态签名/常量行 + 命中符号源码）
  vam_coder_v1.2_F                        （D：完整系统参照）
规模：48 × 4 × R=5 = 960 episodes；seed=20261110；S5=8,000,000；max_tokens=2048。
in-process 调用 run_episode_arm（VSO Phase2 同款），策略包装 = 进程内 monkeypatch，
生产代码零修改。支持 --validate-ctx（无模型形态断言）与断点续跑。
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import random
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parents[1]
ROOT = P1.parent
sys.path.insert(0, str(P1 / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

import p1_common as _p1c  # noqa: E402
from p1_common import SYSTEM_PROMPT, build_messages  # noqa: E402
from vam_coder.config import AppConfig  # noqa: E402
from v12.workspace_audit import (  # noqa: E402
    write_episode_workspace_evidence, write_post_and_diff,
)

import run_p1_v12 as R  # noqa: E402
import dualtoken_strategies as DT  # noqa: E402

PREREG_SHA256 = "088898a3aec9d08411864ea03ff79ac7ff3e78411ed34a58de89ecd0881cc7ed"
P1_TASKS_SHA256 = "d44445b2b8bff0a4338e9694194384235f73d0ea20b3d9550ae5d297c6f8f33b"
ADDENDUM_SHA256 = "d664d602fc3c82a9494c4eed7108e22f5ac272bff41ae732414ef3d60aa2a088"
SYS_PROMPT_SHA256 = "4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a"
BUILD_MSG_SHA256 = "f0b477b0046282739ba1309e5035b2beb2f2f8d2564535d7154019a9aee9e436"

RANDOMIZATION_SEED = 20261110
BOOTSTRAP_SEED = 20261102
REPS = [1, 2, 3, 4, 5]
S5_LIMIT = 8_000_000

TASKS_JSON = P1 / "tasks_p1_validation" / "p1_tasks.json"

ARCHS = [
    {"arch": "dualtoken_A_inline_full_context", "arm": "F",
     "baseline_dir": "vam_coder_v1.2_F", "mode": "inline_full", "no_oprime": True,
     "hypothesis": "A−D 机制对照：不做跨轮复用的上界成本"},
    {"arch": "dualtoken_B_symbolic_addressing", "arm": "F",
     "baseline_dir": "vam_coder_v1.2_F", "mode": "symbolic", "no_oprime": False,
     "hypothesis": "H-B: prompt(D−B)>0 且 ESR 非劣(−12pp)"},
    {"arch": "dualtoken_C_static_rep_plus_symbolic_id", "arm": "F",
     "baseline_dir": "vam_coder_v1.2_F", "mode": "static+address", "no_oprime": False,
     "hypothesis": "H-C: prompt(D−C)>0 且 ESR 非劣(−12pp)"},
    {"arch": "vam_coder_v1.2_F", "arm": "F",
     "baseline_dir": "vam_coder_v1.2_F", "mode": "reference", "no_oprime": False,
     "hypothesis": "D 系统参照（非单变量）"},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def verify_frozen() -> list[str]:
    import inspect
    problems = []
    checks = [
        ("prereg_v1", P1 / "docs" / "v12f_validation_preregistration.md", PREREG_SHA256),
        ("p1_tasks", TASKS_JSON, P1_TASKS_SHA256),
        ("dualtoken_addendum", P1 / "docs" / "v12f_validation_preregistration_addendum_dualtoken.md", ADDENDUM_SHA256),
        ("p1_common", Path(_p1c.__file__), None),  # 记录即可，见 run_meta
    ]
    for name, path, want in checks:
        if want and _sha(path) != want:
            problems.append(f"{name} sha mismatch")
    if _sha_text(SYSTEM_PROMPT) != _sha_text(SYSTEM_PROMPT) :  # placeholder no-op
        pass
    if hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest() != SYS_PROMPT_SHA256:
        problems.append("SYSTEM_PROMPT sha mismatch")
    if _sha_text(inspect.getsource(build_messages)) != BUILD_MSG_SHA256:
        problems.append("build_messages sha mismatch")
    mf = json.loads((P1 / "tasks_p1_validation" / "p1_tasks_manifest.json").read_text(encoding="utf-8"))
    if mf.get("p1_tasks_sha256") != P1_TASKS_SHA256:
        problems.append("p1_tasks_manifest.tasks_sha mismatch")
    return problems


class Args:
    """run_episode_arm 所需参数（与 P1 冻结配置一致）。"""
    def __init__(self, endpoint: str, model: str, *, dry: bool, no_oprime: bool):
        self.closure_depth = 2
        self.budget_tokens = 4096
        self.context_window = 8192
        self.max_history_chars = 24000
        self.temperature = 0.0
        self.seed = 0
        self.max_tokens = 2048
        self.timeout = 300.0
        self.eval_timeout = 60.0
        self.dry_run = dry
        self.history_policy = "keep"
        self.pause_seconds = 0.0
        self.no_oprime = no_oprime
        self.no_must_closure = False
        self.endpoint = endpoint
        self.model = model


def build_episodes(task_ids: list[str]) -> list[dict]:
    return [
        {"episode_id": f"{t}_{a['arch']}_R{r}", "task_id": t,
         "arch": a["arch"], "repetition": r, "spec": a}
        for t in task_ids
        for a in ARCHS
        for r in REPS
    ]


# ---------------------------------------------------------------- 形态校验
VALIDATE_TASKS = ["p1_S02b", "p1_M01a", "p1_S01a"]


def run_validate(cfg: AppConfig) -> int:
    """无模型 dry-run：四组形态断言（补记 §6 门 1）。"""
    tasks_doc = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in tasks_doc["episodes"]}
    R.TASKS_ROOT = TASKS_JSON.parent
    DT.install()
    all_problems: list[str] = []
    out_root = HERE / "validate_ctx"
    if out_root.exists():
        shutil.rmtree(out_root, ignore_errors=True)
    for spec in ARCHS:
        mode = spec["mode"]
        for tid in VALIDATE_TASKS:
            ep_id = f"{tid}_{spec['arch']}_VALIDATE"
            ep_dir = out_root / ep_id
            ep_dir.mkdir(parents=True, exist_ok=True)
            DT.set_mode(mode)
            args = Args("http://127.0.0.1:9/v1", "dry", dry=True,
                        no_oprime=spec["no_oprime"])
            try:
                R.run_episode_arm(
                    episode=by_id[tid], arm=spec["arm"],
                    out_dir=ep_dir / "runner_out", model="dry", endpoint=args.endpoint,
                    args=args, cfg=copy.deepcopy(cfg), rep=0,
                )
            except Exception as e:  # noqa: BLE001
                all_problems.append(f"{spec['arch']}/{tid}: runner exception {e!r}")
                continue
            steps = sorted((ep_dir / "runner_out" / "episodes" / tid /
                            spec["baseline_dir"] / "steps").glob("step*"))
            aud = (ep_dir / "runner_out" / "episodes" / tid /
                   spec["baseline_dir"] / "logs" / "injection_audit.jsonl")
            probs = DT.validate_task_context(steps, mode, tid, aud)
            all_problems += [f"{spec['arch']}/{tid}: {x}" for x in probs]
    DT.restore()
    result = {
        "validated_arms": [a["arch"] for a in ARCHS],
        "tasks": VALIDATE_TASKS,
        "problems": all_problems,
        "pass": not all_problems,
        "note": "动态交付断言（step1 修改→step2 上下文含新值）在实跑分析中执行（补记 §2/§6）",
    }
    (HERE / "validate_ctx_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not all_problems else 1


# ---------------------------------------------------------------- 正式执行
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="https://maas.qianwenaiapi.com/compatible-mode/v1")
    ap.add_argument("--model", default="deepseek-v4.1-flash-1017")
    ap.add_argument("--out", default=str(HERE))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--validate-ctx", action="store_true")
    args = ap.parse_args(argv)

    cfg = AppConfig.load(ROOT / "config" / "default.json")

    if args.validate_ctx:
        return run_validate(cfg)

    problems = verify_frozen()
    if problems:
        print("FROZEN CHECK FAILED:", file=sys.stderr)
        for x in problems:
            print(" -", x, file=sys.stderr)
        return 3

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    log_path = out_root / "execution_log.jsonl"
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
    by_id = {e["id"]: e for e in tasks_doc["episodes"]}
    task_ids = list(by_id)
    episodes = build_episodes(task_ids)
    assert len(episodes) == 960, len(episodes)
    R.TASKS_ROOT = TASKS_JSON.parent

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
            "schema": "dualtoken-randomization-v1",
            "random_seed": RANDOMIZATION_SEED,
            "randomization_method": "python random.Random(seed).shuffle",
            "episode_count": 960,
            "original_episode_order": [e["episode_id"] for e in episodes],
            "randomized_episode_order": [e["episode_id"] for e in order],
            "architectures": [a["arch"] for a in ARCHS],
            "repetitions": REPS, "tasks": 48,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not (out_root / "run_meta.json").exists():
        (out_root / "run_meta.json").write_text(json.dumps({
            "schema": "dualtoken-run-meta-v1",
            "created_at": now(),
            "round": "dualtoken_ablation",
            "prereg": {"path": "p1/docs/v12f_validation_preregistration.md",
                       "sha256": PREREG_SHA256},
            "addendum": {"path": "p1/docs/v12f_validation_preregistration_addendum_dualtoken.md",
                         "sha256": ADDENDUM_SHA256},
            "task_set": {"path": str(TASKS_JSON), "sha256": P1_TASKS_SHA256},
            "arms": {a["arch"]: {"mode": a["mode"], "no_oprime": a["no_oprime"],
                                 "hypothesis": a["hypothesis"]} for a in ARCHS},
            "repetitions": REPS, "episodes_planned": 960, "requests_planned_max": 5500,
            "max_tokens": 2048, "s5_token_limit": S5_LIMIT,
            "s5_basis": "2× 估算≈4M（P1 每集均值×960 外推）",
            "randomization_seed": RANDOMIZATION_SEED, "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_B": 10000,
            "frozen_hashes": {
                "system_prompt_sha256": _sha_text(SYSTEM_PROMPT),
                "build_messages_source_sha256": _sha_text(__import__("inspect").getsource(build_messages)),
                "p1_common_sha256": _sha(Path(_p1c.__file__)),
            },
            "model": args.model, "endpoint": args.endpoint,
            "temperature": 0.0, "seed": 0, "history_policy": "keep",
            "production_code_modified": False,
            "implementation": "orchestrator 进程内 monkeypatch（dualtoken_strategies.py）",
            "python": sys.executable,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    logs = out_root / "episode_logs"
    logs.mkdir(exist_ok=True)
    DT.install()

    cumulative = prior_tokens
    executed = ok_n = fail_n = 0
    stop_code = stop_reason = ""
    limit = args.limit if args.limit > 0 else len(order)

    for i, ep in enumerate(order, 1):
        if ep["episode_id"] in done:
            continue
        if executed >= limit:
            break
        ep_id, task, arch, rep = ep["episode_id"], ep["task_id"], ep["arch"], ep["repetition"]
        spec = ep["spec"]
        ep_dir = logs / ep_id
        ep_dir.mkdir(parents=True, exist_ok=True)
        runner_out = ep_dir / "runner_out"
        if runner_out.exists():
            shutil.rmtree(runner_out, ignore_errors=True)
            print(f"  [resume-cleanup] partial removed: {ep_id}", flush=True)
        write_episode_workspace_evidence(
            source_project=TASKS_JSON.parent / task / "project",
            workspace=ep_dir / "workspace_pending", episode_dir=ep_dir,
            episode_id=ep_id, task_id=task, arm=arch, repetition=rep,
        )
        DT.set_mode(spec["mode"])
        run_args = Args(args.endpoint, args.model, dry=False,
                         no_oprime=spec["no_oprime"])
        t0 = time.time()
        try:
            rows = R.run_episode_arm(
                episode=by_id[task], arm=spec["arm"], out_dir=runner_out,
                model=args.model, endpoint=args.endpoint,
                args=run_args, cfg=copy.deepcopy(cfg), rep=rep,
            )
            status, rc = "OK", 0
        except Exception as e:  # noqa: BLE001
            rows, status, rc = [], f"EXC_{type(e).__name__}", 1
            print(f"  episode exception {ep_id}: {e!r}", flush=True)
        elapsed = round(time.time() - t0, 2)
        ep_tokens = sum(int(r.get("prompt_tokens") or 0) + int(r.get("completion_tokens") or 0)
                        for r in rows)
        ep_req = sum(1 for r in rows
                     if (r.get("usage_source") or "none") != "none"
                     or int(r.get("prompt_tokens") or 0) > 0)
        cumulative += ep_tokens
        executed += 1
        if status == "OK":
            ok_n += 1
        else:
            fail_n += 1
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
            "repetition": rep, "order_index": i, "status": status, "rc": rc,
            "elapsed_s": elapsed, "steps": len(rows), "requests": ep_req,
            "tokens": ep_tokens, "mode": spec["mode"], "ts": now(),
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if executed % 10 == 0 or status != "OK":
            print(f"[{executed}/{limit}] {ep_id} -> {status} steps={len(rows)} "
                  f"tok={ep_tokens} cum={cumulative}", flush=True)
        if cumulative > S5_LIMIT:
            stop_code, stop_reason = "S5", f"cumulative {cumulative} > {S5_LIMIT}"
            print(f"STOP S5: {stop_reason}", flush=True)
            break
        time.sleep(0.5)

    DT.set_mode("reference")
    summary = {
        "finished_at": now(), "planned": 960,
        "done_total": len(done) + ok_n, "executed_new": executed,
        "ok_new": ok_n, "fail_new": fail_n, "cumulative_tokens": cumulative,
        "s5_limit": S5_LIMIT, "randomization_seed": RANDOMIZATION_SEED,
        "stop_code": stop_code, "stop_reason": stop_reason,
        "resumed": bool(done),
    }
    (out_root / "execution_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))
    return 0 if not stop_code else 4


if __name__ == "__main__":
    raise SystemExit(main())
