#!/usr/bin/env python
"""V1.3-M2 Holdout 分析：raw_results → metrics → bootstrap → failure_analysis。

冻结统计口径（rev3 §3.3 / prereg §7）：
  bootstrap seed = 20261102, B = 10000, cluster = task_id（同 task 全部 rep+全部臂）
  NA 规则：TPSE 零成功 = NA（不记 0）；报告 NA 样本比例。
输入：p1/experiments/v13_holdout_validation/runs/
输出：raw_results.csv, metrics_summary.csv, bootstrap_results.csv,
      failure_analysis.csv, analysis_manifest.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
P1 = HERE.parents[1]
sys.path.insert(0, str(P1 / "scripts"))
from p1_common import parse_file_blocks  # noqa: E402

RUNS = HERE / "episode_logs"
TASKS_DIR = P1 / "tasks_v13_holdout"
ARMS = ["E", "F", "V13A"]
BOOTSTRAP_SEED = 20261102
BOOTSTRAP_B = 10000
REV3_SHA256 = "8ceed45d6554ba952a641fbbebb49b4f3eb0f69858c16ba9d58d7025eb9ee13f"

BASELINE_DIR = {"E": "vam_coder_v1.2_E", "F": "vam_coder_v1.2_F", "V13A": "vam_coder_v1.3_V13A"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def load_steps() -> tuple[list[dict], dict[tuple, dict], dict[str, dict]]:
    """返回 (step_rows, audit_by_key, episode_meta)。"""
    steps: list[dict] = []
    audits: dict[tuple, dict] = {}
    ep_meta: dict[str, dict] = {}
    for ep_dir in sorted((RUNS).iterdir()):
        if not ep_dir.is_dir():
            continue
        ep_id = ep_dir.name
        parts = ep_id.rsplit("_R", 1)
        rep = int(parts[1])
        core = parts[0]
        arm = "V13A" if core.endswith("_V13A") else core.rsplit("_", 1)[-1]
        task = core[: -(len(arm) + 1)]
        per_step = ep_dir / "runner_out" / "per_step.csv"
        if not per_step.exists():
            continue
        with per_step.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        rows.sort(key=lambda r: r["step"])
        ep_meta[ep_id] = {
            "episode_id": ep_id, "task_id": task, "arm": arm, "rep": rep,
            "steps": rows,
        }
        # injection audit
        aud_path = ep_dir / "runner_out" / "episodes" / task / BASELINE_DIR[arm] / "logs" / "injection_audit.jsonl"
        if aud_path.exists():
            for line in aud_path.read_text(encoding="utf-8").splitlines():
                a = json.loads(line)
                audits[(task, arm, rep, a["step"])] = a
        for r in rows:
            steps.append({
                "episode_id": ep_id, "task_id": task, "arm": arm, "rep": rep,
                **{k: r[k] for k in r},
            })
    return steps, audits, ep_meta


def episode_metrics(ep_meta: dict[str, dict]) -> dict[str, dict]:
    out = {}
    for ep_id, m in ep_meta.items():
        rows = m["steps"]
        succ = all(r["eval_success"] == "1" for r in rows)
        prompt = sum(int(r["prompt_tokens"] or 0) for r in rows)
        comp = sum(int(r["completion_tokens"] or 0) for r in rows)
        cached = sum(int(r["cached_tokens"] or 0) for r in rows)
        out[ep_id] = {
            **{k: m[k] for k in ("episode_id", "task_id", "arm", "rep")},
            "success": int(succ),
            "steps": len(rows),
            "steps_passed": sum(1 for r in rows if r["eval_success"] == "1"),
            "prompt_tokens": prompt,
            "completion_tokens": comp,
            "cached_tokens": cached,
            "total_tokens": prompt + comp,
            "requests": sum(
                1 for r in rows
                if (r.get("usage_source") or "none") != "none" or int(r["prompt_tokens"] or 0) > 0
            ),
            "insufficient": sum(int(r["insufficient"] or 0) for r in rows),
            "errors": [r["error"] for r in rows if r["error"]],
            "eval_results": [r["eval_success"] for r in rows],
            "step_ids": [r["step"] for r in rows],
        }
    return out


def classify_failures(ep_meta, audits) -> list[dict]:
    """失败 episode 分类：error_class（rev3 §4.5）+ 模型机制（RQ4）。"""
    proj_cache: dict[str, dict[str, str]] = {}
    records: list[dict] = []
    for ep_id, m in sorted(ep_meta.items()):
        task, arm, rep = m["task_id"], m["arm"], m["rep"]
        rows = m["steps"]
        failed_steps = [r["step"] for r in rows if r["eval_success"] != "1"]
        if not failed_steps:
            continue
        # 工作区状态回放（逐步比较模型输出与改前内容）
        if task not in proj_cache:
            root = TASKS_DIR / task / "project"
            proj_cache[task] = {
                p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
                for p in root.rglob("*.py")
            }
        state = dict(proj_cache[task])
        mechanisms = []
        error_class = "none"
        details = []
        for r in rows:
            step = r["step"]
            sdir = RUNS / ep_id / "runner_out" / "episodes" / task / BASELINE_DIR[arm] / "steps" / step
            resp_path = sdir / "response.txt"
            text = resp_path.read_text(encoding="utf-8") if resp_path.exists() else ""
            ins = int(r["insufficient"] or 0)
            err = r["error"] or ""
            if ins:
                if error_class == "none":
                    error_class = "none"  # INSUFFICIENT 单列状态（无请求）
                mechanisms.append("insufficient_no_request")
                details.append(f"{step}:INSUFFICIENT:{r['insufficient_reason']}")
            elif err and "dry_run" not in err:
                if "refused" in err.lower() or "timeout" in err.lower() or "connection" in err.lower():
                    error_class = "infrastructure" if error_class == "none" else error_class
                mechanisms.append("infrastructure_error")
                details.append(f"{step}:{err[:120]}")
            elif r["eval_success"] != "1":
                has_file = "FILE:" in text
                has_noedit = "NO_EDIT" in text
                if not has_file and has_noedit:
                    mechanisms.append("model_no_edit")
                    details.append(f"{step}:NO_EDIT but eval failed")
                elif not has_file and not has_noedit:
                    if error_class == "none":
                        error_class = "protocol"
                    mechanisms.append("protocol_violation")
                    details.append(f"{step}:response neither FILE nor NO_EDIT")
                else:
                    blocks = parse_file_blocks(text)
                    applied_now = []
                    changed = []
                    for rel, content in blocks:
                        rel = str(rel).replace("\\", "/")
                        if not rel:
                            continue
                        applied_now.append(rel)
                        prev = state.get(rel)
                        if prev is None or content.strip() == prev.strip():
                            continue
                        changed.append(rel)
                    if applied_now and not changed:
                        mechanisms.append("model_noop")
                        details.append(f"{step}:FILE emitted but content unchanged ({','.join(applied_now)})")
                    elif r["eval_success"] == "0":
                        mechanisms.append("model_wrong_implementation")
                        details.append(f"{step}:changed {','.join(changed) or applied_now} but eval failed")
                    # 回放状态（用实际落盘内容更准：读 workspace）
                    ws = sdir.parents[1] / "workspace"
                    for rel in applied_now:
                        wp = ws / rel
                        if wp.exists():
                            state[rel] = wp.read_text(encoding="utf-8")
            else:
                ws = sdir.parents[1] / "workspace"
                for rel in list(state):
                    wp = ws / rel
                    if wp.exists():
                        state[rel] = wp.read_text(encoding="utf-8")
        # 无 error 且非协议 → 模型能力（rev3 §4.5 之外的常规 eval 失败）
        records.append({
            "episode_id": ep_id,
            "task_id": task,
            "arm": arm,
            "repetition": rep,
            "episode_success": 0,
            "failed_steps": ";".join(failed_steps),
            "eval_results": ";".join(r["eval_success"] for r in rows),
            "error_class": error_class,
            "mechanisms": ";".join(mechanisms),
            "detail": " | ".join(details)[:500],
            "response_step1": str(RUNS / ep_id / "runner_out" / "episodes" / task / BASELINE_DIR[arm] / "steps" / rows[0]["step"] / "response.txt"),
            "eval_output_step1": str(RUNS / ep_id / "runner_out" / "episodes" / task / BASELINE_DIR[arm] / "steps" / rows[0]["step"] / "eval_output.txt"),
        })
    return records


def main() -> int:
    steps, audits, ep_meta = load_steps()
    assert len(ep_meta) == 72, len(ep_meta)
    assert len(steps) == 144, len(steps)
    eps = episode_metrics(ep_meta)

    # ---------------- raw_results.csv（步级，144 行）
    raw_fields = [
        "episode_id", "task_id", "arm", "rep", "step", "eval_success",
        "prompt_tokens", "completion_tokens", "cached_tokens", "total_tokens",
        "usage_source", "context_file_blocks", "context_digest_lines",
        "n_verified_safe_omissions", "insufficient", "insufficient_reason",
        "must_full_count", "edit_targets", "inspected_related_full", "adaptive_rows",
        "adaptive_full", "dho", "pre_send_ok",
        "t_model_ms", "t_eval_ms", "t_step_ms", "t_assemble_ms", "context_chars",
        "applied_files", "error", "config_sha256",
    ]
    with (HERE / "raw_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=raw_fields, extrasaction="ignore")
        w.writeheader()
        for r in steps:
            key = (r["task_id"], r["arm"], int(r["rep"]), r["step"])
            a = audits.get(key, {})
            plan = a.get("plan", {})
            post = a.get("post", {})
            pre = a.get("pre_send", {})
            levels = a.get("levels", [])
            related_full = sum(1 for x in levels if x["r"] >= 1 and x["level"] == "FULL")
            related_n = sum(1 for x in levels if x["r"] >= 1)
            aa = plan.get("adaptive_audit", []) or []
            et = set(plan.get("edit_targets", []))
            om = set(post.get("omitted_files", []))
            row = dict(r)
            row.update({
                "edit_targets": ";".join(plan.get("edit_targets", [])),
                "inspected_related_full": f"{related_full}/{related_n}",
                "adaptive_rows": len(aa),
                "adaptive_full": sum(1 for x in aa if x.get("level") == "FULL"),
                "dho": int(bool(et & om)),
                "pre_send_ok": int(bool(pre.get("ok", True))),
            })
            w.writerow({k: row.get(k, "") for k in raw_fields})

    # ---------------- metrics_summary.csv
    ep_elapsed: dict[str, float] = {}
    log_path = HERE / "execution_log.jsonl"
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if "elapsed_s" in rec:
                ep_elapsed[rec["episode_id"]] = float(rec["elapsed_s"])

    def metric_block(label, key, arm_filter=None, task_filter=None):
        sel = [
            e for e in eps.values()
            if (arm_filter is None or e["arm"] == arm_filter)
            and (task_filter is None or e["task_id"] == task_filter)
        ]
        n = len(sel)
        succ = sum(e["success"] for e in sel)
        steps_n = sum(e["steps"] for e in sel)
        steps_p = sum(e["steps_passed"] for e in sel)
        prompt = sum(e["prompt_tokens"] for e in sel)
        comp = sum(e["completion_tokens"] for e in sel)
        cached = sum(e["cached_tokens"] for e in sel)
        total = prompt + comp
        esr = succ / n if n else "NA"
        lo, hi = wilson_ci(succ, n) if n else (float("nan"), float("nan"))
        tpae = total / n if n else "NA"
        tpse = total / succ if succ else "NA"
        n_fail = n - succ
        fetc_t = sum(e["total_tokens"] for e in sel if not e["success"])
        fetc_m = fetc_t / n_fail if n_fail else "NA"
        ins_steps = sum(e["insufficient"] for e in sel)
        # 步级注入统计
        f_exp = f_dig = f_non = must_sum = 0
        ad_rows = ad_full = ad_hit = 0
        n_steps_aud = 0
        for e in sel:
            for s in e["step_ids"]:
                a = audits.get((e["task_id"], e["arm"], e["rep"], s))
                if not a:
                    continue
                n_steps_aud += 1
                for c in a.get("checks", []):
                    if c["action"] == "EXPAND":
                        f_exp += 1
                    elif c["action"] == "DIGEST":
                        f_dig += 1
                    elif c["action"] == "NONE":
                        f_non += 1
                plan = a.get("plan", {})
                must_sum += int(plan.get("must_full_count", 0))
                aa = plan.get("adaptive_audit", []) or []
                ad_rows += len(aa)
                ad_full += sum(1 for x in aa if x.get("level") == "FULL")
                ad_hit += sum(
                    1 for x in aa
                    if "instruction_hit" in (x.get("reason") or "")
                    or "dependency_touch" in (x.get("reason") or "")
                )
        ep_requests = [e["requests"] for e in sel]
        errs = sum(len(e["errors"]) for e in sel)
        elapsed = [ep_elapsed[e["episode_id"]] for e in sel if e["episode_id"] in ep_elapsed]
        return {
            "scope": label, "key": key,
            "episodes": n, "success": succ,
            "ESR": f"{esr:.4f}" if isinstance(esr, float) else esr,
            "ESR_ci95_low": f"{lo:.4f}", "ESR_ci95_high": f"{hi:.4f}",
            "steps": steps_n, "steps_passed": steps_p,
            "SPR": f"{steps_p / steps_n:.4f}" if steps_n else "NA",
            "prompt_tokens_total": prompt,
            "prompt_tokens_mean_per_episode": f"{prompt / n:.1f}" if n else "NA",
            "prompt_tokens_mean_per_request": f"{prompt / sum(ep_requests):.1f}" if sum(ep_requests) else "NA",
            "completion_tokens_total": comp,
            "cached_tokens_total": cached,
            "total_tokens": total,
            "TPAE": f"{tpae:.1f}" if isinstance(tpae, float) else tpae,
            "TPSE": f"{tpse:.1f}" if isinstance(tpse, float) else tpse,
            "FETC_total": fetc_t,
            "FETC_mean": f"{fetc_m:.1f}" if isinstance(fetc_m, float) else fetc_m,
            "requests_mean_per_episode": f"{np.mean(ep_requests):.2f}" if n else "NA",
            "elapsed_s_mean_per_episode": f"{np.mean(elapsed):.2f}" if elapsed else "NA",
            "elapsed_s_total": f"{sum(elapsed):.2f}" if elapsed else "NA",
            "insufficient_steps": ins_steps,
            "insufficient_ratio": f"{ins_steps / steps_n:.4f}" if steps_n else "NA",
            "runner_error_rows": errs,
            "steps_audited": n_steps_aud,
            "inject_full_total": f_exp, "inject_digest_total": f_dig, "inject_none_total": f_non,
            "full_rate_per_step": f"{f_exp / n_steps_aud:.3f}" if n_steps_aud else "NA",
            "digest_rate_per_step": f"{f_dig / n_steps_aud:.3f}" if n_steps_aud else "NA",
            "must_full_mean_per_step": f"{must_sum / n_steps_aud:.2f}" if n_steps_aud else "NA",
            "adaptive_rows": ad_rows, "adaptive_full": ad_full,
            "adaptive_upgrade_rate": f"{ad_full / ad_rows:.3f}" if ad_rows else "NA",
            "adaptive_hit_or_touch_reason_rows": ad_hit,
            "dho_total": sum(
                1 for e in sel for s in e["step_ids"]
                if audits.get((e["task_id"], e["arm"], e["rep"], s), {})
                .get("plan", {}).get("edit_targets")
                and set(audits[(e["task_id"], e["arm"], e["rep"], s)]["plan"]["edit_targets"])
                & set(audits[(e["task_id"], e["arm"], e["rep"], s)].get("post", {}).get("omitted_files", []))
            ),
        }

    blocks = []
    for arm in ARMS:
        blocks.append(metric_block(arm_filter=arm, label="arm", key=arm))
    for task in sorted({e["task_id"] for e in eps.values()}):
        for arm in ARMS:
            blocks.append(metric_block(arm_filter=arm, task_filter=task, label="task_arm", key=f"{task}:{arm}"))

    # 失败机制分布（补列）
    fail_recs = classify_failures(ep_meta, audits)
    mech_by_arm = defaultdict(Counter)
    for fr in fail_recs:
        for mech in fr["mechanisms"].split(";"):
            if mech:
                mech_by_arm[fr["arm"]][mech] += 1
    errclass_by_arm = defaultdict(Counter)
    for fr in fail_recs:
        errclass_by_arm[fr["arm"]][fr["error_class"]] += 1

    mech_cols = sorted({m for c in mech_by_arm.values() for m in c})
    for b in blocks:
        if b["scope"] == "arm":
            c = mech_by_arm[b["key"]]
            for m in mech_cols:
                b[f"fail_mech_{m}"] = c.get(m, 0)
            b["fail_errorclass_protocol"] = errclass_by_arm[b["key"]].get("protocol", 0)
            b["fail_errorclass_infrastructure"] = errclass_by_arm[b["key"]].get("infrastructure", 0)
            b["fail_errorclass_architecture"] = errclass_by_arm[b["key"]].get("architecture", 0)
            b["fail_errorclass_none_model_capability"] = errclass_by_arm[b["key"]].get("none", 0)

    fields: list[str] = []
    for b in blocks:
        for k in b:
            if k not in fields:
                fields.append(k)
    with (HERE / "metrics_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for b in blocks:
            w.writerow(b)

    # ---------------- failure_analysis.csv
    ff = list(fail_recs[0].keys()) if fail_recs else ["episode_id"]
    with (HERE / "failure_analysis.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ff)
        w.writeheader()
        for fr in fail_recs:
            w.writerow(fr)

    # ---------------- bootstrap_results.csv（task cluster, seed=20261102, B=10000）
    task_ids = sorted({e["task_id"] for e in eps.values()})
    by_ta: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in eps.values():
        by_ta[(e["task_id"], e["arm"])].append(e)

    def stats_for(sample_tasks, arm):
        sel = [e for t in sample_tasks for e in by_ta[(t, arm)]]
        n = len(sel)
        succ = sum(e["success"] for e in sel)
        total = sum(e["total_tokens"] for e in sel)
        prompt = sum(e["prompt_tokens"] for e in sel)
        esr = succ / n
        tpae = total / n
        tpse = (total / succ) if succ else None  # NA
        ppe = prompt / n
        return {"ESR": esr, "TPAE": tpae, "TPSE": tpse, "prompt_per_episode": ppe}

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    metric_names = ["ESR", "TPAE", "TPSE", "prompt_per_episode"]
    pairs = [("V13A", "E"), ("V13A", "F"), ("F", "E")]
    boot = {("arm", a, m): [] for a in ARMS for m in metric_names}
    boot.update({("delta", f"{p1}-{p2}", m): [] for p1, p2 in pairs for m in metric_names})
    for _ in range(BOOTSTRAP_B):
        sample = rng.choice(task_ids, size=len(task_ids), replace=True).tolist()
        s_stats = {a: stats_for(sample, a) for a in ARMS}
        for a in ARMS:
            for m in metric_names:
                boot[("arm", a, m)].append(s_stats[a][m])
        for p1, p2 in pairs:
            for m in metric_names:
                v1, v2 = s_stats[p1][m], s_stats[p2][m]
                boot[("delta", f"{p1}-{p2}", m)].append(None if (v1 is None or v2 is None) else v1 - v2)

    point = {a: stats_for(task_ids, a) for a in ARMS}
    rows_b = []

    def ci_of(vals):
        finite = [v for v in vals if v is not None]
        na = len(vals) - len(finite)
        if not finite:
            return "NA", "NA", na
        arr = np.asarray(finite, dtype=float)
        return f"{np.percentile(arr, 2.5):.6f}", f"{np.percentile(arr, 97.5):.6f}", na

    for a in ARMS:
        for m in metric_names:
            lo, hi, na = ci_of(boot[("arm", a, m)])
            pv = point[a][m]
            rows_b.append({
                "scope": "arm_point", "key": a, "metric": m,
                "point": "NA" if pv is None else f"{pv:.6f}",
                "ci95_low": lo, "ci95_high": hi,
                "n_bootstrap": BOOTSTRAP_B, "na_samples": na,
                "na_ratio": f"{na / BOOTSTRAP_B:.4f}",
                "bootstrap_seed": BOOTSTRAP_SEED, "cluster": "task_id",
            })
    for p1, p2 in pairs:
        for m in metric_names:
            v1, v2 = point[p1][m], point[p2][m]
            pt = None if (v1 is None or v2 is None) else v1 - v2
            lo, hi, na = ci_of(boot[("delta", f"{p1}-{p2}", m)])
            rows_b.append({
                "scope": "paired_delta", "key": f"{p1}-{p2}", "metric": m,
                "point": "NA" if pt is None else f"{pt:.6f}",
                "ci95_low": lo, "ci95_high": hi,
                "n_bootstrap": BOOTSTRAP_B, "na_samples": na,
                "na_ratio": f"{na / BOOTSTRAP_B:.4f}",
                "bootstrap_seed": BOOTSTRAP_SEED, "cluster": "task_id",
            })
    bf = ["scope", "key", "metric", "point", "ci95_low", "ci95_high",
          "n_bootstrap", "na_samples", "na_ratio", "bootstrap_seed", "cluster"]
    with (HERE / "bootstrap_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=bf)
        w.writeheader()
        w.writerows(rows_b)

    # ---------------- analysis_manifest.json
    manifest = {
        "schema": "v13-analysis-manifest-v1",
        "generated_at": now(),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_B": BOOTSTRAP_B,
        "cluster": "task_id",
        "stat_unit_note": "同 task 全部 rep + 全部臂整体重采样（72 episodes ≠ 72 独立样本）",
        "na_rule": "TPSE 零成功样本 = NA（不记 0）；na_ratio 已报告",
        "rev3_sha256": REV3_SHA256,
        "inputs": {
            "runs_dir": str(RUNS),
            "holdout_tasks_sha256": hashlib.sha256((TASKS_DIR / "holdout_tasks.json").read_bytes()).hexdigest(),
        },
        "outputs": ["raw_results.csv", "metrics_summary.csv", "bootstrap_results.csv", "failure_analysis.csv"],
        "step_rows": len(steps), "episodes": len(ep_meta),
        "failed_episodes": len(fail_recs),
    }
    (HERE / "analysis_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
