#!/usr/bin/env python
"""P0.1 离线审计：解析 v1.2 dry-run 审计日志 + d=1/d=2 闭包对比。

只读现有 run 目录与 tasks；不调用模型。
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = P1_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from vam_coder.config import AppConfig  # noqa: E402
from vam_coder.invalidation import InvalidationManager  # noqa: E402
from vam_coder.logging_util import JsonlLogger  # noqa: E402
from vam_coder.store import StaticStore  # noqa: E402

from p1_common import posix  # noqa: E402
from v12.levels import dependency_closure  # noqa: E402


def load_audits(run_dir: Path) -> list[dict]:
    rows = []
    for p in sorted(run_dir.glob("episodes/*/*/logs/injection_audit.jsonl")):
        parts = p.parts
        # .../episodes/<task>/<baseline>/logs/...
        try:
            ei = parts.index("episodes")
            task, baseline = parts[ei + 1], parts[ei + 2]
        except ValueError:
            continue
        arm = baseline.rsplit("_", 1)[-1] if baseline.startswith("vam_coder_v1.2_") else baseline
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            r["_arm"] = arm
            r["_task"] = task
            r["_baseline"] = baseline
            rows.append(r)
    return rows


def pct(vals: list[float], q: float) -> float:
    if not vals:
        return float("nan")
    s = sorted(vals)
    idx = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[idx]


def file_deps_from_store(store: StaticStore, repo_id: str) -> dict[str, set[str]]:
    symbols = store.list_symbols(repo_id)
    id_to_file = {sid: posix(e.file_path) for sid, e in symbols.items()}
    deps: dict[str, set[str]] = {posix(e.file_path) for e in symbols.values()}  # type: ignore
    deps = {}
    for e in symbols.values():
        rel = posix(e.file_path)
        deps.setdefault(rel, set())
        for dep in e.deps or []:
            if dep in id_to_file:
                deps[rel].add(id_to_file[dep])
            elif isinstance(dep, str) and dep.endswith(".py"):
                deps[rel].add(posix(dep))
    return deps


def offline_closure_stats(tasks_meta: list[dict], depth: int) -> list[dict]:
    """对每个任务：以 edit 文件集近似 targets（project 内全部 py 为粗集会偏大）——
    使用 dry-run E 臂 must 中非 risk 的部分不精确；此处用「全部非 tombstone 文件」
    的闭包规模作为上界，以及「文件数」分布，便于 d=1 vs d=2 相对比较。
    """
    import shutil
    import tempfile

    out = []
    cfg = AppConfig()
    for ep in tasks_meta:
        eid = ep["id"]
        proj = P1_ROOT / "tasks" / eid / "project"
        td = Path(tempfile.mkdtemp(prefix="p01_"))
        try:
            ws = td / "ws"
            shutil.copytree(proj, ws)
            db = td / "s.db"
            cfg.db_path = str(db)
            cfg.decision_log = str(td / "d.jsonl")
            cfg.invalidation_log = str(td / "i.jsonl")
            store = StaticStore(db)
            man = InvalidationManager(store, cfg, JsonlLogger(cfg.invalidation_log))
            man.sync(ws, eid)
            deps = file_deps_from_store(store, eid)
            files = sorted({posix(e.file_path) for e in store.list_symbols(eid).values()})
            full = dependency_closure(set(files), {}, deps, depth=depth)
            # release sqlite
            for attr in ("conn", "_conn", "connection"):
                c = getattr(store, attr, None)
                if c is not None and hasattr(c, "close"):
                    try:
                        c.close()
                    except Exception:
                        pass
            out.append(
                {
                    "task_id": eid,
                    "depth": depth,
                    "n_files": len(files),
                    "closure_from_all": len(full),
                    "closure_delta": len(full) - len(files),
                }
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--run-dir",
        default=str(P1_ROOT / "results" / "runs" / "v12_p01_dryrun_24tasks_EFGH_full"),
    )
    ap.add_argument("--out", default=str(P1_ROOT / "results" / "v1.2_p01_audit.json"))
    args = ap.parse_args()
    run_dir = Path(args.run_dir)
    rows = load_audits(run_dir)
    print(f"audits loaded: {len(rows)}")

    # per step1 only for d stats (step2 must may shrink via O')
    step1 = [r for r in rows if r.get("step") == "step1"]
    by_arm_task: dict[tuple[str, str], dict] = {}
    for r in step1:
        key = (r["_arm"], r["_task"])
        by_arm_task[key] = r

    must_counts = []
    closure_sizes = []
    insuff = []
    over_k = []
    over_b = []
    per_task_rows = []
    violations = []

    tasks = sorted({r["_task"] for r in step1})
    arms = ["E", "F", "G", "H"]

    for task in tasks:
        must_sets = {}
        for arm in arms:
            r = by_arm_task.get((arm, task))
            if not r:
                violations.append(f"missing {arm}/{task}")
                continue
            plan = r["plan"]
            levels = r["levels"]
            must_sets[arm] = set(plan.get("must_full") or [])
            must_counts.append(len(plan.get("must_full") or []))
            closure_sizes.append(
                len(set(plan.get("must_full") or []) )  # must as proxy for closure-included
            )
            if plan.get("insufficient"):
                insuff.append((arm, task, plan.get("insufficient_reasons")))
            if plan.get("over_kmax"):
                over_k.append((arm, task))
            if plan.get("over_budget"):
                over_b.append((arm, task))

            # H: non-must must be NONE
            if arm == "H":
                for lv in levels:
                    if not lv.get("is_must") and lv["level"] != "NONE":
                        violations.append(f"H non-must not NONE: {task} {lv}")
            # E: related non-must digest or none
            if arm == "E":
                for lv in levels:
                    if not lv.get("is_must") and lv["level"] == "FULL":
                        # optional full only if kmax keep - should not exist if related is digest policy
                        violations.append(f"E non-must FULL: {task} {lv}")
            # F: related non-must full or none (no digest)
            if arm == "F":
                for lv in levels:
                    if not lv.get("is_must") and lv["level"] == "DIGEST":
                        violations.append(f"F has DIGEST: {task} {lv}")

        # must identical across arms
        if must_sets:
            ref = next(iter(must_sets.values()))
            for arm, ms in must_sets.items():
                if ms != ref:
                    violations.append(f"must mismatch {task} {arm}: {ms} vs {ref}")

        # O' summary E
        e = by_arm_task.get(("E", task))
        oprime = []
        if e:
            for c in e.get("checks") or []:
                if c.get("verified_safe_omission"):
                    oprime.append(c.get("file"))

        per_task_rows.append(
            {
                "task_id": task,
                "must_full_E": sorted(must_sets.get("E", set())),
                "must_full_count": len(must_sets.get("E", set())),
                "levels_E": {
                    lv["path"]: lv["level"]
                    for lv in (e["levels"] if e else [])
                },
                "levels_H": {
                    lv["path"]: lv["level"]
                    for lv in (by_arm_task.get(("H", task)) or {}).get("levels", [])
                },
                "oprime_E_step1": oprime,
                "required_context_E": (e or {}).get("plan", {}).get("required_context_tokens_est"),
                "available_context": (e or {}).get("plan", {}).get("available_context_tokens"),
            }
        )

    # offline d=1 vs d=2
    meta = json.loads((P1_ROOT / "tasks" / "tasks_v1.0.json").read_text(encoding="utf-8"))
    d1 = offline_closure_stats(meta["episodes"], 1)
    d2 = offline_closure_stats(meta["episodes"], 2)

    def summarize(counts: list[int]) -> dict:
        if not counts:
            return {}
        return {
            "n": len(counts),
            "mean": statistics.mean(counts),
            "median": statistics.median(counts),
            "max": max(counts),
            "p90": pct(counts, 0.90),
            "min": min(counts),
        }

    # must from E step1 only
    must_e = [len(by_arm_task[("E", t)]["plan"]["must_full"]) for t in tasks if ("E", t) in by_arm_task]
    report = {
        "run_dir": str(run_dir),
        "n_audit_rows": len(rows),
        "n_tasks": len(tasks),
        "n_step1_arms": len(by_arm_task),
        "must_full_E_step1": summarize(must_e),
        "over_kmax_n": len(over_k),
        "over_budget_n": len(over_b),
        "insufficient_n": len(insuff),
        "insufficient": insuff,
        "violations": violations,
        "per_task": per_task_rows,
        "d1_closure": d1,
        "d2_closure": d2,
        "d_diff": [
            {
                "task_id": a["task_id"],
                "n_files": a["n_files"],
                "c1": a["closure_from_all"],
                "c2": b["closure_from_all"],
                "delta_2_minus_1": b["closure_from_all"] - a["closure_from_all"],
            }
            for a, b in zip(d1, d2)
        ],
    }
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")
    print("violations", len(violations))
    print("must E summary", report["must_full_E_step1"])
    print("over_k", len(over_k), "over_b", len(over_b), "insuf", len(insuff))
    deltas = [x["delta_2_minus_1"] for x in report["d_diff"]]
    print("d2-d1 closure delta mean", statistics.mean(deltas) if deltas else None, "max", max(deltas) if deltas else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
