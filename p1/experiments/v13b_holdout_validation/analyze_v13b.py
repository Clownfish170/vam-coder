#!/usr/bin/env python
"""V1.3-B Round 2 分析：5 架构（全名标注）→ raw/metrics/bootstrap/failure。

统计口径与 round1 一致：bootstrap seed=20261102, B=10000, cluster=task_id；
TPSE 零成功=NA 并报告 na_ratio。架构名一律完整英文标识。
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

LOGS = HERE / "episode_logs"
TASKS_DIR = P1 / "tasks_v13_holdout"
BOOTSTRAP_SEED = 20261102
BOOTSTRAP_B = 10000

ARCHS = [
    "vam_coder_v1.2_E",
    "vam_coder_v1.2_F",
    "vam_coder_v1.3_V13B",
    "memory_off",
    "symbol_full_read",
]
VAM_ARCHS = {"vam_coder_v1.2_E", "vam_coder_v1.2_F", "vam_coder_v1.3_V13B"}
# 架构 → runner 输出内的基线目录名
BASELINE_DIR = {
    "vam_coder_v1.2_E": "vam_coder_v1.2_E",
    "vam_coder_v1.2_F": "vam_coder_v1.2_F",
    "vam_coder_v1.3_V13B": "vam_coder_v1.3_V13B",
    "memory_off": "memory_off",
    "symbol_full_read": "symbol_full_read",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_ep_id(ep_id: str, task_ids: list[str]) -> tuple[str, str, int]:
    core, rep_s = ep_id.rsplit("_R", 1)
    task = max((t for t in task_ids if core.startswith(t + "_")), key=len)
    arch = core[len(task) + 1:]
    return task, arch, int(rep_s)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def load_all():
    tasks_doc = json.loads((TASKS_DIR / "holdout_tasks.json").read_text(encoding="utf-8"))
    task_ids = [e["id"] for e in tasks_doc["episodes"]]

    steps: list[dict] = []
    audits: dict[tuple, dict] = {}
    ep_meta: dict[str, dict] = {}
    for ep_dir in sorted(LOGS.iterdir()):
        if not ep_dir.is_dir():
            continue
        task, arch, rep = parse_ep_id(ep_dir.name, task_ids)
        bdir = BASELINE_DIR[arch]
        per_step = ep_dir / "runner_out" / "per_step.csv"
        if not per_step.exists():
            continue
        with per_step.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        rows.sort(key=lambda r: r["step"])
        # cached_tokens：v12 列；p1 从 result.json.raw_usage 补
        for r in rows:
            if "cached_tokens" not in r:
                rj = ep_dir / "runner_out" / "episodes" / task / bdir / "steps" / r["step"] / "result.json"
                cached = 0
                if rj.exists():
                    d = json.loads(jz := rj.read_text(encoding="utf-8"))
                    ptd = ((d.get("raw_usage") or {}).get("prompt_tokens_details")) or {}
                    cached = int(ptd.get("cached_tokens") or 0)
                r["cached_tokens"] = str(cached)
            r["architecture"] = arch
        ep_meta[ep_dir.name] = {
            "episode_id": ep_dir.name, "task_id": task, "architecture": arch,
            "rep": rep, "baseline_dir": bdir, "steps": rows,
        }
        aud_path = ep_dir / "runner_out" / "episodes" / task / bdir / "logs" / "injection_audit.jsonl"
        if aud_path.exists():
            for line in aud_path.read_text(encoding="utf-8").splitlines():
                a = json.loads(line)
                audits[(task, arch, rep, a["step"])] = a
        for r in rows:
            steps.append({
                "episode_id": ep_dir.name, "task_id": task, "architecture": arch,
                "rep": rep, **{k: r.get(k, "") for k in r},
            })
    return steps, audits, ep_meta, task_ids


def episode_metrics(ep_meta) -> dict[str, dict]:
    out = {}
    for ep_id, m in ep_meta.items():
        rows = m["steps"]
        succ = all(r.get("eval_success") == "1" for r in rows)
        prompt = sum(int(r.get("prompt_tokens") or 0) for r in rows)
        comp = sum(int(r.get("completion_tokens") or 0) for r in rows)
        cached = sum(int(r.get("cached_tokens") or 0) for r in rows)
        out[ep_id] = {
            **{k: m[k] for k in ("episode_id", "task_id", "architecture", "rep")},
            "success": int(succ),
            "steps": len(rows),
            "steps_passed": sum(1 for r in rows if r.get("eval_success") == "1"),
            "prompt_tokens": prompt,
            "completion_tokens": comp,
            "cached_tokens": cached,
            "total_tokens": prompt + comp,
            "requests": sum(
                1 for r in rows
                if (r.get("usage_source") or "none") != "none" or int(r.get("prompt_tokens") or 0) > 0
            ),
            "errors": [r.get("error") for r in rows if r.get("error")],
            "step_ids": [r["step"] for r in rows],
        }
    return out


def classify_failures(ep_meta) -> list[dict]:
    proj_cache: dict[str, dict[str, str]] = {}
    records: list[dict] = []
    for ep_id, m in sorted(ep_meta.items()):
        task, arch, rep = m["task_id"], m["architecture"], m["rep"]
        rows = m["steps"]
        failed_steps = [r["step"] for r in rows if r.get("eval_success") != "1"]
        if not failed_steps:
            continue
        if task not in proj_cache:
            root = TASKS_DIR / task / "project"
            proj_cache[task] = {
                p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
                for p in root.rglob("*.py")
            }
        state = dict(proj_cache[task])
        mechanisms, details = [], []
        for r in rows:
            step = r["step"]
            sdir = LOGS / ep_id / "runner_out" / "episodes" / task / BASELINE_DIR[arch] / "steps" / step
            resp_path = sdir / "response.txt"
            text = resp_path.read_text(encoding="utf-8") if resp_path.exists() else ""
            err = r.get("error") or ""
            if r.get("eval_success") == "1":
                ws = sdir.parents[1] / "workspace"
                for rel in list(state):
                    wp = ws / rel
                    if wp.exists():
                        state[rel] = wp.read_text(encoding="utf-8")
                continue
            if err and "dry_run" not in err:
                mechanisms.append("infrastructure_error")
                details.append(f"{step}:{err[:120]}")
                continue
            has_file, has_noedit = "FILE:" in text, "NO_EDIT" in text
            if not has_file and has_noedit:
                mechanisms.append("model_no_edit")
                details.append(f"{step}:NO_EDIT")
            elif not has_file and not has_noedit:
                mechanisms.append("protocol_violation")
                details.append(f"{step}:neither FILE nor NO_EDIT")
            else:
                blocks = parse_file_blocks(text)
                applied_now, changed = [], []
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
                    details.append(f"{step}:unchanged {','.join(applied_now)}")
                else:
                    mechanisms.append("model_wrong_implementation")
                    details.append(f"{step}:changed {','.join(changed) or ','.join(applied_now)}")
                ws = sdir.parents[1] / "workspace"
                for rel in applied_now:
                    wp = ws / rel
                    if wp.exists():
                        state[rel] = wp.read_text(encoding="utf-8")
        records.append({
            "episode_id": ep_id, "task_id": task, "architecture": arch,
            "repetition": rep, "episode_success": 0,
            "failed_steps": ";".join(failed_steps),
            "eval_results": ";".join(r.get("eval_success") or "" for r in rows),
            "mechanisms": ";".join(mechanisms),
            "detail": " | ".join(details)[:500],
            "response_step1": str(LOGS / ep_id / "runner_out" / "episodes" / task / BASELINE_DIR[arch] / "steps" / rows[0]["step"] / "response.txt"),
            "eval_output_step1": str(LOGS / ep_id / "runner_out" / "episodes" / task / BASELINE_DIR[arch] / "steps" / rows[0]["step"] / "eval_output.txt"),
        })
    return records


def main() -> int:
    steps, audits, ep_meta, task_ids = load_all()
    assert len(ep_meta) == 120, len(ep_meta)
    assert len(steps) == 240, len(steps)
    eps = episode_metrics(ep_meta)

    ep_elapsed: dict[str, float] = {}
    log_path = HERE / "execution_log.jsonl"
    for line in log_path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if "elapsed_s" in rec:
            ep_elapsed[rec["episode_id"]] = float(rec["elapsed_s"])

    # ---------------- raw_results.csv
    raw_fields = [
        "episode_id", "task_id", "architecture", "rep", "step", "eval_success",
        "prompt_tokens", "completion_tokens", "cached_tokens", "total_tokens",
        "usage_source", "context_file_blocks", "context_digest_lines",
        "n_verified_safe_omissions", "insufficient", "must_full_count",
        "edit_targets", "adaptive_rows", "adaptive_full", "v13b_none_no_body",
        "dho", "pre_send_ok", "t_model_ms", "t_eval_ms", "t_step_ms",
        "context_chars", "applied_files", "error",
    ]
    with (HERE / "raw_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=raw_fields, extrasaction="ignore")
        w.writeheader()
        for r in steps:
            key = (r["task_id"], r["architecture"], int(r["rep"]), r["step"])
            a = audits.get(key)
            row = {k: r.get(k, "") for k in raw_fields}
            if a is None:
                # 非 VAM 架构：注入决策类字段无定义 → NA（≠0）
                row.update({
                    "insufficient": "NA", "must_full_count": "NA",
                    "edit_targets": "NA", "adaptive_rows": "NA",
                    "adaptive_full": "NA", "v13b_none_no_body": "NA",
                    "dho": "NA", "pre_send_ok": "NA",
                    "context_digest_lines": r.get("context_digest_lines", "0") or "0",
                })
            else:
                plan = a.get("plan", {})
                post = a.get("post", {})
                pre = a.get("pre_send", {})
                aa = plan.get("adaptive_audit", []) or []
                et = set(plan.get("edit_targets", []))
                om = set(post.get("omitted_files", []))
                v13b_none = sum(
                    1 for x in a.get("levels", [])
                    if str(x.get("reason", "")).startswith("v13b_no_body")
                )
                row.update({
                    "insufficient": r.get("insufficient", "0"),
                    "must_full_count": plan.get("must_full_count", ""),
                    "edit_targets": ";".join(plan.get("edit_targets", [])),
                    "adaptive_rows": len(aa),
                    "adaptive_full": sum(1 for x in aa if x.get("level") == "FULL"),
                    "v13b_none_no_body": v13b_none,
                    "dho": int(bool(et & om)),
                    "pre_send_ok": int(bool(pre.get("ok", True))),
                })
            w.writerow(row)

    # ---------------- failure_analysis.csv
    fail_recs = classify_failures(ep_meta)
    ff = list(fail_recs[0].keys()) if fail_recs else ["episode_id"]
    with (HERE / "failure_analysis.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ff)
        w.writeheader()
        for fr in fail_recs:
            w.writerow(fr)

    # ---------------- metrics_summary.csv
    def block(label, key, arch_filter=None, task_filter=None):
        sel = [
            e for e in eps.values()
            if (arch_filter is None or e["architecture"] == arch_filter)
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
        esr = succ / n if n else float("nan")
        lo, hi = wilson_ci(succ, n) if n else (float("nan"), float("nan"))
        tpae = total / n if n else float("nan")
        tpse = (total / succ) if succ else None
        n_fail = n - succ
        fetc_t = sum(e["total_tokens"] for e in sel if not e["success"])
        fetc_m = fetc_t / n_fail if n_fail else None
        reqs = [e["requests"] for e in sel]
        elapsed = [ep_elapsed[e["episode_id"]] for e in sel if e["episode_id"] in ep_elapsed]
        # 注入统计（仅 VAM 架构；非 VAM = NA）
        is_vam = (arch_filter in VAM_ARCHS) if arch_filter else None
        if is_vam:
            f_exp = f_dig = f_none_adt = must_sum = 0
            ad_rows = ad_full = v13b_none_rows = n_aud = 0
            ins_steps = dho = 0
            for e in sel:
                for s in e["step_ids"]:
                    a = audits.get((e["task_id"], e["architecture"], e["rep"], s))
                    if not a:
                        continue
                    n_aud += 1
                    for c in a.get("checks", []):
                        if c["action"] == "EXPAND":
                            f_exp += 1
                        elif c["action"] == "DIGEST":
                            f_dig += 1
                        elif c["action"] == "NONE":
                            f_none_adt += 1
                    plan = a.get("plan", {})
                    must_sum += int(plan.get("must_full_count", 0))
                    aa = plan.get("adaptive_audit", []) or []
                    ad_rows += len(aa)
                    ad_full += sum(1 for x in aa if x.get("level") == "FULL")
                    v13b_none_rows += sum(
                        1 for x in a.get("levels", [])
                        if str(x.get("reason", "")).startswith("v13b_no_body")
                    )
                    ins_steps += int(a.get("post", {}).get("insufficient", 0))
                    dho += int(bool(set(plan.get("edit_targets", [])) & set(a.get("post", {}).get("omitted_files", []))))
            inj = {
                "inject_full_total": f_exp, "inject_digest_total": f_dig,
                "inject_none_total": f_none_adt,
                "full_rate_per_step": f"{f_exp / n_aud:.3f}" if n_aud else "NA",
                "digest_rate_per_step": f"{f_dig / n_aud:.3f}" if n_aud else "NA",
                "must_full_mean_per_step": f"{must_sum / n_aud:.2f}" if n_aud else "NA",
                "adaptive_rows": ad_rows, "adaptive_full": ad_full,
                "v13b_none_no_body_total": v13b_none_rows,
                "insufficient_steps": ins_steps,
                "insufficient_ratio": f"{ins_steps / steps_n:.4f}",
                "dho_total": dho, "pre_send_fail_total": 0,
            }
        else:
            inj = {
                "inject_full_total": "NA（非VAM无注入决策）", "inject_digest_total": "NA",
                "inject_none_total": "NA", "full_rate_per_step": "NA",
                "digest_rate_per_step": "NA", "must_full_mean_per_step": "NA",
                "adaptive_rows": "NA", "adaptive_full": "NA",
                "v13b_none_no_body_total": "NA",
                "insufficient_steps": "NA", "insufficient_ratio": "NA",
                "dho_total": "NA", "pre_send_fail_total": "NA",
            }
        return {
            "scope": label, "key": key, "episodes": n, "success": succ,
            "ESR": f"{esr:.4f}", "ESR_ci95_low": f"{lo:.4f}", "ESR_ci95_high": f"{hi:.4f}",
            "steps": steps_n, "steps_passed": steps_p,
            "SPR": f"{steps_p / steps_n:.4f}" if steps_n else "NA",
            "prompt_tokens_total": prompt,
            "prompt_tokens_mean_per_episode": f"{prompt / n:.1f}" if n else "NA",
            "completion_tokens_total": comp, "cached_tokens_total": cached,
            "total_tokens": total,
            "TPAE": f"{tpae:.1f}",
            "TPSE": f"{tpse:.1f}" if tpse is not None else "NA",
            "FETC_total": fetc_t,
            "FETC_mean": f"{fetc_m:.1f}" if fetc_m is not None else "NA",
            "requests_mean_per_episode": f"{np.mean(reqs):.2f}" if n else "NA",
            "elapsed_s_mean_per_episode": f"{np.mean(elapsed):.2f}" if elapsed else "NA",
            **inj,
        }

    blocks = [block("architecture", a, arch_filter=a) for a in ARCHS]
    for t in sorted({e["task_id"] for e in eps.values()}):
        for a in ARCHS:
            blocks.append(block("task_architecture", f"{t}:{a}", arch_filter=a, task_filter=t))

    mech_by = defaultdict(Counter)
    for fr in fail_recs:
        for mech in fr["mechanisms"].split(";"):
            if mech:
                mech_by[fr["architecture"]][mech] += 1
    mech_cols = sorted({m for c in mech_by.values() for m in c})
    for b in blocks:
        if b["scope"] == "architecture":
            c = mech_by[b["key"]]
            for m in mech_cols:
                b[f"fail_mech_{m}"] = c.get(m, 0)
            b["failed_episodes"] = sum(
                1 for fr in fail_recs if fr["architecture"] == b["key"]
            )
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

    # ---------------- bootstrap_results.csv
    by_ta: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in eps.values():
        by_ta[(e["task_id"], e["architecture"])].append(e)

    def stats_for(sample_tasks, arch):
        sel = [e for t in sample_tasks for e in by_ta[(t, arch)]]
        n = len(sel)
        succ = sum(e["success"] for e in sel)
        total = sum(e["total_tokens"] for e in sel)
        prompt = sum(e["prompt_tokens"] for e in sel)
        return {
            "ESR": succ / n,
            "TPAE": total / n,
            "TPSE": (total / succ) if succ else None,
            "prompt_per_episode": prompt / n,
        }

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    metric_names = ["ESR", "TPAE", "TPSE", "prompt_per_episode"]
    pairs = [
        ("vam_coder_v1.3_V13B", "vam_coder_v1.2_E"),
        ("vam_coder_v1.3_V13B", "vam_coder_v1.2_F"),
        ("vam_coder_v1.3_V13B", "memory_off"),
        ("vam_coder_v1.3_V13B", "symbol_full_read"),
        ("vam_coder_v1.2_F", "vam_coder_v1.2_E"),
        ("memory_off", "symbol_full_read"),
    ]
    boot = {("arch", a, m): [] for a in ARCHS for m in metric_names}
    boot.update({("delta", f"{p1}−{p2}", m): [] for p1, p2 in pairs for m in metric_names})
    for _ in range(BOOTSTRAP_B):
        sample = rng.choice(task_ids, size=len(task_ids), replace=True).tolist()
        s_stats = {a: stats_for(sample, a) for a in ARCHS}
        for a in ARCHS:
            for m in metric_names:
                boot[("arch", a, m)].append(s_stats[a][m])
        for p1, p2 in pairs:
            for m in metric_names:
                v1, v2 = s_stats[p1][m], s_stats[p2][m]
                boot[("delta", f"{p1}−{p2}", m)].append(
                    None if (v1 is None or v2 is None) else v1 - v2
                )

    point = {a: stats_for(task_ids, a) for a in ARCHS}
    rows_b = []

    def ci_of(vals):
        finite = [v for v in vals if v is not None]
        na = len(vals) - len(finite)
        if not finite:
            return "NA", "NA", na
        arr = np.asarray(finite, dtype=float)
        return f"{np.percentile(arr, 2.5):.6f}", f"{np.percentile(arr, 97.5):.6f}", na

    for a in ARCHS:
        for m in metric_names:
            lo, hi, na = ci_of(boot[("arch", a, m)])
            pv = point[a][m]
            rows_b.append({
                "scope": "architecture_point", "key": a, "metric": m,
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
            lo, hi, na = ci_of(boot[("delta", f"{p1}−{p2}", m)])
            rows_b.append({
                "scope": "paired_delta", "key": f"{p1}−{p2}", "metric": m,
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

    manifest = {
        "schema": "v13b-analysis-manifest-v1",
        "generated_at": now(),
        "round": "round2_v13b",
        "architectures": ARCHS,
        "architecture_naming": "完整英文标识；结果文件不缩写、不翻译",
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_B": BOOTSTRAP_B,
        "cluster": "task_id",
        "na_rule": "TPSE 零成功样本 = NA（不记 0）；na_ratio 已报告；非 VAM 架构注入决策字段 = NA",
        "inputs": {
            "episode_logs": str(LOGS),
            "holdout_tasks_sha256": hashlib.sha256(
                (TASKS_DIR / "holdout_tasks.json").read_bytes()
            ).hexdigest(),
        },
        "outputs": ["raw_results.csv", "metrics_summary.csv",
                    "bootstrap_results.csv", "failure_analysis.csv"],
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
