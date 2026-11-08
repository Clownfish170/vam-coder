#!/usr/bin/env python
"""P1 statistical analysis + failure attribution (read-only on raw data).

Reproducible: seed 20261102, B=10000 task-cluster bootstrap.
Writes only to p1/experiments/v12_p1_execution/analysis/.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path("p1/experiments/v12_p1_execution")
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(exist_ok=True)
SEED = 20261102
B_BOOT = 10000
ARMS = ["A", "B", "D", "E", "F", "G", "H"]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((center - half) / denom, (center + half) / denom)


def main() -> None:
    inputs = {
        "per_step_all": ROOT / "per_step_all.csv",
        "summary_by_arm": ROOT / "summary_by_arm.csv",
        "randomization": ROOT / "randomization_manifest.json",
        "execution_summary": ROOT / "execution_summary.json",
        "prereg": Path("p1/docs/v1.2_experiment_preregistration.md"),
    }
    for k, p in inputs.items():
        if not p.exists():
            raise SystemExit(f"missing input {k}: {p}")

    df = pd.read_csv(inputs["per_step_all"])
    # normalize error empty
    df["error"] = df["error"].fillna("")
    df["eval_success"] = pd.to_numeric(df["eval_success"], errors="coerce")

    # ---------- Integrity ----------
    n_steps = len(df)
    n_eps = df.groupby(["arm", "task", "rep"]).ngroups
    tasks = sorted(df.task.unique())
    arms = sorted(df.arm.unique())
    reps = sorted(df.rep.unique())
    steps_per = df.groupby(["arm", "task", "rep"]).size()
    integrity = {
        "n_steps": int(n_steps),
        "n_episodes": int(n_eps),
        "n_tasks": len(tasks),
        "arms": arms,
        "reps": [int(r) for r in reps],
        "all_2_steps": bool((steps_per == 2).all()),
        "prompt_gt0": int((df.prompt_tokens > 0).sum()),
        "dup_episode_step": int(
            df.duplicated(["episode_id", "step"]).sum()
        ),
        "eval_na": int(df.eval_success.isna().sum()),
        "tasks": tasks,
    }
    # expected coverage
    expected_cells = {(t, a, r) for t in tasks for a in arms for r in reps}
    actual_cells = set(
        zip(df.task, df.arm, df.rep.astype(int))
    )
    integrity["missing_cells"] = sorted(expected_cells - actual_cells)
    integrity["extra_cells"] = sorted(actual_cells - expected_cells)

    rm = json.loads(inputs["randomization"].read_text(encoding="utf-8"))
    order_ids = rm["randomized_episode_order"]
    run_eps = sorted(df.episode_id.unique())
    integrity["rand_n"] = rm["episode_count"]
    integrity["rand_unique"] = len(set(order_ids))
    integrity["episodes_match_rand"] = set(run_eps) == set(order_ids)

    # workspace
    pre = list(ROOT.glob("runs/*/workspace_pre_manifest.json"))
    post = list(ROOT.glob("runs/*/workspace_post_manifest.json"))
    diffs = list(ROOT.glob("runs/*/workspace_diff.json"))
    integrity["ws_pre"] = len(pre)
    integrity["ws_post"] = len(post)
    integrity["ws_diff"] = len(diffs)

    # ---------- Episode metrics ----------
    ep = (
        df.groupby(["arm", "task", "rep"], as_index=False)
        .agg(
            both=("eval_success", lambda s: int((s == 1).all()) if s.notna().all() and len(s) == 2 else 0),
            n_steps=("eval_success", "count"),
            step_pass=("eval_success", lambda s: int((s == 1).sum())),
            tot=("total_tokens", "sum"),
            prompt=("prompt_tokens", "sum"),
            comp=("completion_tokens", "sum"),
        )
    )

    def arm_stats(a: str) -> dict:
        g = ep[ep.arm == a]
        ns = int(g.both.sum())
        n = len(g)
        fail = g[g.both == 0]
        spr_pass = int(g.step_pass.sum())
        spr_n = int(g.n_steps.sum())
        lo, hi = wilson_ci(ns, n)
        return {
            "arm": a,
            "episodes": n,
            "successes": ns,
            "ESR": ns / n if n else float("nan"),
            "ESR_wilson_lo": lo,
            "ESR_wilson_hi": hi,
            "SPR": spr_pass / spr_n if spr_n else float("nan"),
            "SPR_num": spr_pass,
            "SPR_den": spr_n,
            "TPAE": g.tot.mean() if n else float("nan"),
            "TPSE": (g.tot.sum() / ns) if ns else float("inf"),
            "FETC_total": int(fail.tot.sum()) if len(fail) else 0,
            "FETC_mean": (fail.tot.mean() if len(fail) else None),
        }

    ci_rows = [arm_stats(a) for a in ARMS]
    ci_df = pd.DataFrame(ci_rows)
    ci_df.to_csv(ANALYSIS / "confidence_intervals.csv", index=False)

    # ---------- Bootstrap (task cluster) ----------
    # Build task-level long table: for each task, for each arm, list of (success, token) per rep
    rng = random.Random(SEED)
    task_list = tasks
    # index data
    by_ta = {}
    for _, r in ep.iterrows():
        by_ta.setdefault((r.task, r.arm), []).append(
            {"succ": int(r.both), "tok": float(r.tot)}
        )

    def esr_of(sample_tasks, arm):
        succ = 0
        n = 0
        for t in sample_tasks:
            for item in by_ta.get((t, arm), []):
                succ += item["succ"]
                n += 1
        return (succ / n) if n else float("nan")

    def tpae_of(sample_tasks, arm):
        toks = [i["tok"] for t in sample_tasks for i in by_ta.get((t, arm), [])]
        return (sum(toks) / len(toks)) if toks else float("nan")

    def tpse_of(sample_tasks, arm):
        toks = [i["tok"] for t in sample_tasks for i in by_ta.get((t, arm), [])]
        succ = [i["succ"] for t in sample_tasks for i in by_ta.get((t, arm), [])]
        ns = sum(succ)
        if ns == 0:
            return None  # NA
        return sum(toks) / ns

    comparisons = [
        ("E", "D", "ESR"),
        ("E", "D", "TPAE"),
        ("E", "D", "TPSE"),
        ("E", "A", "ESR"),
        ("E", "A", "TPAE"),
        ("E", "A", "TPSE"),
        ("E", "F", "ESR"),
        ("E", "G", "ESR"),
        ("E", "H", "ESR"),
    ]

    # point estimates
    def delta_stat(a1, a0, metric):
        s1 = arm_stats(a1)
        s0 = arm_stats(a0)
        if metric == "ESR":
            return s1["ESR"] - s0["ESR"]
        if metric == "TPAE":
            return s1["TPAE"] - s0["TPAE"]
        if metric == "TPSE":
            v1, v0 = s1["TPSE"], s0["TPSE"]
            if v1 is None or v0 is None or v1 == float("inf") or v0 == float("inf"):
                return float("nan")
            return v1 - v0
        return float("nan")

    boot_rows = []
    na_tpse = {c: 0 for c in comparisons}
    # pre-sample indices for reproducibility: one sequence of task draws per b
    for b in range(B_BOOT):
        sample = [task_list[rng.randrange(len(task_list))] for _ in range(len(task_list))]
        for a1, a0, metric in comparisons:
            if metric == "ESR":
                d = esr_of(sample, a1) - esr_of(sample, a0)
            elif metric == "TPAE":
                d = tpae_of(sample, a1) - tpae_of(sample, a0)
            else:
                v1 = tpse_of(sample, a1)
                v0 = tpse_of(sample, a0)
                if v1 is None or v0 is None:
                    na_tpse[(a1, a0, metric)] += 1
                    d = float("nan")
                else:
                    d = v1 - v0
            boot_rows.append(
                {
                    "b": b,
                    "cmp": f"{a1}-{a0}",
                    "metric": metric,
                    "delta": d,
                }
            )
    boot = pd.DataFrame(boot_rows)

    summary_rows = []
    for a1, a0, metric in comparisons:
        sub = boot[(boot.cmp == f"{a1}-{a0}") & (boot.metric == metric)]
        deltas = sub.delta.dropna().astype(float)
        pe = delta_stat(a1, a0, metric)
        if len(deltas) == 0:
            lo = hi = float("nan")
            n_valid = 0
        else:
            lo = float(deltas.quantile(0.025))
            hi = float(deltas.quantile(0.975))
            n_valid = int(len(deltas))
        summary_rows.append(
            {
                "comparison": f"{a1}-{a0}",
                "metric": metric,
                "point_estimate": pe,
                "boot_ci_lo": lo,
                "boot_ci_hi": hi,
                "boot_n_valid": n_valid,
                "boot_n_na": int(na_tpse.get((a1, a0, metric), 0)),
                "boot_n_total": B_BOOT,
            }
        )
    boot_summary = pd.DataFrame(summary_rows)
    boot_summary.to_csv(ANALYSIS / "bootstrap_results.csv", index=False)
    # also save compact delta distribution stats
    boot.to_csv(ANALYSIS / "bootstrap_deltas_sample.csv", index=False)

    # ---------- Gate decisions (prereg §6) ----------
    sE, sD, sA = arm_stats("E"), arm_stats("D"), arm_stats("A")
    eps_d, eps_a, tpse_th, tpae_th = 0.10, 0.15, 0.95, 1.05

    def get_boot(a1, a0, metric):
        row = boot_summary[
            (boot_summary.comparison == f"{a1}-{a0}") & (boot_summary.metric == metric)
        ]
        if row.empty:
            return None
        return row.iloc[0]

    gates = []

    def add_gate(gid, desc, point_ok, ci_lo, ci_hi, threshold_text, evidence):
        gates.append(
            {
                "gate_id": gid,
                "description": desc,
                "point_estimate_pass": point_ok,
                "ci_lo": ci_lo,
                "ci_hi": ci_hi,
                "threshold": threshold_text,
                "evidence_sufficiency": evidence,
            }
        )

    # G1 ESR E vs D non-inferiority point
    d_esr = sE["ESR"] - sD["ESR"]
    g1_point = d_esr >= -eps_d
    b1 = get_boot("E", "D", "ESR")
    add_gate(
        "G1_ESR_E_vs_D",
        f"ESR_E >= ESR_D - {eps_d}",
        g1_point,
        b1.boot_ci_lo if b1 is not None else float("nan"),
        b1.boot_ci_hi if b1 is not None else float("nan"),
        f"ΔESR >= -{eps_d}",
        "point_only" if g1_point and b1 is not None and b1.boot_ci_lo < -eps_d else ("point_and_ci" if g1_point else "fail_point"),
    )

    # G2 ESR E vs A
    d_esr_a = sE["ESR"] - sA["ESR"]
    g2_point = d_esr_a >= -eps_a
    b2 = get_boot("E", "A", "ESR")
    add_gate(
        "G2_ESR_E_vs_A",
        f"ESR_E >= ESR_A - {eps_a}",
        g2_point,
        b2.boot_ci_lo if b2 is not None else float("nan"),
        b2.boot_ci_hi if b2 is not None else float("nan"),
        f"ΔESR >= -{eps_a}",
        "point_only" if g2_point and b2 is not None and b2.boot_ci_lo < -eps_a else ("point_and_ci" if g2_point else "fail_point"),
    )

    # G3 TPSE E <= 0.95 D (ratio) - use delta TPSE <= -0.05 * TPSE_D
    thr_tpse_d = -0.05 * sD["TPSE"]
    d_tpse_d = sE["TPSE"] - sD["TPSE"]
    g3_point = sE["TPSE"] <= tpse_th * sD["TPSE"]
    b3 = get_boot("E", "D", "TPSE")
    add_gate(
        "G3_TPSE_E_vs_D",
        f"TPSE_E <= {tpse_th} * TPSE_D (Δ <= {thr_tpse_d:.2f})",
        g3_point,
        b3.boot_ci_lo if b3 is not None else float("nan"),
        b3.boot_ci_hi if b3 is not None else float("nan"),
        f"ΔTPSE <= {thr_tpse_d:.2f}",
        "point_only" if g3_point and b3 is not None and b3.boot_ci_hi > thr_tpse_d else ("point_and_ci" if g3_point else "fail_point"),
    )

    # G4 TPAE E <= 1.05 D
    g4_point = sE["TPAE"] <= tpae_th * sD["TPAE"]
    b4 = get_boot("E", "D", "TPAE")
    thr_tpae_d = 0.05 * sD["TPAE"]
    add_gate(
        "G4_TPAE_E_vs_D",
        f"TPAE_E <= {tpae_th} * TPAE_D (Δ <= {thr_tpae_d:.2f})",
        g4_point,
        b4.boot_ci_lo if b4 is not None else float("nan"),
        b4.boot_ci_hi if b4 is not None else float("nan"),
        f"ΔTPAE <= {thr_tpae_d:.2f}",
        "point_only" if g4_point and b4 is not None and b4.boot_ci_hi > thr_tpae_d else ("point_and_ci" if g4_point else "fail_point"),
    )

    # G5-G7 vs A cost claims
    thr_tpse_a = -0.05 * sA["TPSE"]
    g5 = sE["TPSE"] <= tpse_th * sA["TPSE"] and g2_point and sE["TPAE"] <= tpae_th * sA["TPAE"]
    b5 = get_boot("E", "A", "TPSE")
    add_gate(
        "G5_E_vs_A_cost_claim",
        "E vs A: ESR+TPSE+TPAE gates for cost claim",
        g5,
        b5.boot_ci_lo if b5 is not None else float("nan"),
        b5.boot_ci_hi if b5 is not None else float("nan"),
        f"TPSE<=0.95*A, TPAE<=1.05*A, ESR>=A-{eps_a}",
        "point_only",
    )

    gates_df = pd.DataFrame(gates)
    gates_df.to_csv(ANALYSIS / "rq_gate_points.csv", index=False)

    # ---------- Failure attribution ----------
    fail_rows = []
    for _, r in df[df.eval_success == 0].iterrows():
        # locate evidence
        ep_id = r.episode_id
        step = r.step
        base = None
        # search runner_out
        cands = list(ROOT.glob(f"runs/{ep_id}/runner_out/episodes/*/*/steps/{step}"))
        if cands:
            base = cands[0]
        resp = ""
        eval_out = ""
        ctx = ""
        if base:
            rp = base / "response.txt"
            if rp.exists():
                resp = rp.read_text(encoding="utf-8", errors="replace")
            epf = base / "eval_output.txt"
            if epf.exists():
                eval_out = epf.read_text(encoding="utf-8", errors="replace")
            cf = base / "context.txt"
            if cf.exists():
                ctx = cf.read_text(encoding="utf-8", errors="replace")
        rs = resp.strip()
        if rs == "NO_EDIT":
            primary = "MODEL_NO_EDIT" if "--- FILE" in ctx else "CONTEXT_MISSING"
        elif "FAILED" in eval_out or "NameError" in eval_out or "assert" in eval_out:
            primary = "MODEL_REASONING_ERROR"
        elif not rs:
            primary = "UNDETERMINED"
        elif not rs.startswith("FILE:") and rs != "NO_EDIT":
            primary = "PROTOCOL_VIOLATION"
        else:
            primary = "UNDETERMINED"
        fail_rows.append(
            {
                "episode_id": ep_id,
                "task_id": r.task,
                "arm": r.arm,
                "rep": int(r.rep),
                "step": step,
                "primary_failure_category": primary,
                "eval_success": int(r.eval_success),
                "response_head": rs[:80].replace("\n", " | "),
                "context_has_file": "--- FILE" in ctx,
                "prompt_tokens": int(r.prompt_tokens),
                "evidence_path": base.as_posix() if base else "",
            }
        )
    fail_df = pd.DataFrame(fail_rows)
    fail_df.to_csv(ANALYSIS / "failure_attribution.csv", index=False)

    fail_by_arm = fail_df.groupby("arm").size().to_dict() if len(fail_df) else {}
    fail_by_cat = fail_df.primary_failure_category.value_counts().to_dict() if len(fail_df) else {}
    fail_by_task = fail_df.task_id.value_counts().to_dict() if len(fail_df) else {}

    # ---------- Integrity report ----------
    integ_md = f"""# P1 Data Integrity Report

Generated: {datetime.now(timezone.utc).isoformat()}

## Coverage
- steps: {integrity['n_steps']} (expect 1008)
- episodes: {integrity['n_episodes']} (expect 504)
- tasks: {integrity['n_tasks']} (expect 24)
- arms: {integrity['arms']}
- reps: {integrity['reps']}
- all 2 steps: {integrity['all_2_steps']}
- missing matrix cells: {integrity['missing_cells']}
- extra cells: {integrity['extra_cells']}
- duplicate episode+step: {integrity['dup_episode_step']}
- eval NA: {integrity['eval_na']}
- prompt>0: {integrity['prompt_gt0']}

## Randomization
- rand n/unique: {integrity['rand_n']}/{integrity['rand_unique']}
- episodes match rand order set: {integrity['episodes_match_rand']}

## Workspace
- pre/post/diff: {integrity['ws_pre']}/{integrity['ws_post']}/{integrity['ws_diff']}

## Notes
- A/B stdout GBK decode warnings during run: recorded as harness I/O issue, not experiment failure (returncode 0, 144 steps each present).
- Raw data not modified.

## Input SHA256
"""
    for k, p in inputs.items():
        integ_md += f"- {k}: `{sha256(p)}` (`{p}`)\n"
    (ANALYSIS / "data_integrity_report.md").write_text(integ_md, encoding="utf-8")

    # ---------- RQ gate decision ----------
    def fmt(x):
        if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
            return "NA"
        return f"{x:.4f}"

    rq = f"""# RQ Gate Decision (prereg §6)

Point estimates use full P1 data. CI from task-cluster bootstrap B={B_BOOT}, seed={SEED}.

## Arm summary (ESR Wilson 95% CI)

| arm | success | ESR | Wilson95 | SPR | TPAE | TPSE | FETC_total | FETC_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
"""
    for r in ci_rows:
        rq += (
            f"| {r['arm']} | {r['successes']}/{r['episodes']} | {r['ESR']:.4f} | "
            f"[{r['ESR_wilson_lo']:.3f},{r['ESR_wilson_hi']:.3f}] | {r['SPR']:.4f} | "
            f"{r['TPAE']:.2f} | {fmt(r['TPSE'])} | {r['FETC_total']} | {fmt(r['FETC_mean'])} |\n"
        )

    rq += "\n## Bootstrap Δ (E − ref), 95% percentile CI\n\n"
    rq += "| cmp | metric | point | CI_lo | CI_hi | valid | NA |\n| --- | --- | --- | --- | --- | --- | --- |\n"
    for _, r in boot_summary.iterrows():
        rq += (
            f"| {r.comparison} | {r.metric} | {fmt(r.point_estimate)} | "
            f"{fmt(r.boot_ci_lo)} | {fmt(r.boot_ci_hi)} | {r.boot_n_valid} | {r.boot_n_na} |\n"
        )

    rq += "\n## Gates (prereg §6.2)\n\n"
    rq += "| gate | point_pass | threshold | CI | evidence |\n| --- | --- | --- | --- | --- |\n"
    for g in gates:
        rq += (
            f"| {g['gate_id']} | {'PASS' if g['point_estimate_pass'] else 'FAIL'} | "
            f"{g['threshold']} | [{fmt(g['ci_lo'])},{fmt(g['ci_hi'])}] | {g['evidence_sufficiency']} |\n"
        )

    # overall gate logic
    all_point = all(g["point_estimate_pass"] for g in gates if g["gate_id"].startswith("G1") or g["gate_id"].startswith("G2") or g["gate_id"] in ("G3_TPSE_E_vs_D", "G4_TPAE_E_vs_D"))
    # CI strength
    g1 = next(g for g in gates if g["gate_id"] == "G1_ESR_E_vs_D")
    g1_ci_ok = g1["ci_lo"] is not None and not (
        isinstance(g1["ci_lo"], float) and math.isnan(g1["ci_lo"])
    ) and g1["ci_lo"] >= -eps_d

    rq += f"""
## Interpretation discipline

- Point-estimate gates: **{'ALL CORE POINT GATES PASS' if all_point else 'SOME POINT GATES FAIL'}**
- G1 CI lower bound >= -{eps_d}: **{'YES' if g1_ci_ok else 'NO / insufficient'}**
- If point passes but CI crosses -ε: phrase only as「点估计满足预注册门禁，把握度不足」——**不得**写 statistically non-inferior.
- cached_tokens is **not** used as KV cache savings evidence.
- Live VP/INSUFFICIENT block was **not** triggered in P0; do not claim live block verified.

## Failure summary (P1 steps)
- total failed steps: {len(fail_df)}
- by category: {fail_by_cat}
- by arm: {fail_by_arm}
- top tasks: {dict(list(fail_by_task.items())[:8])}
"""
    (ANALYSIS / "rq_gate_decision.md").write_text(rq, encoding="utf-8")

    # ---------- Final statistical report ----------
    final = f"""# P1 Final Statistical Report (V1.2-r2.2)

Read-only analysis. Seed={SEED}, bootstrap B={B_BOOT}, task-cluster (all R kept per sampled task).

## Integrity
See data_integrity_report.md. episodes={integrity['n_episodes']}, steps={integrity['n_steps']}, ws={integrity['ws_pre']}/{integrity['ws_post']}/{integrity['ws_diff']}.

## Primary metrics

"""
    for r in ci_rows:
        final += (
            f"- **{r['arm']}**: ESR {r['successes']}/{r['episodes']} = {r['ESR']:.3f} "
            f"(Wilson [{r['ESR_wilson_lo']:.3f},{r['ESR_wilson_hi']:.3f}]); "
            f"SPR {r['SPR_num']}/{r['SPR_den']}; TPAE {r['TPAE']:.1f}; "
            f"TPSE {fmt(r['TPSE'])}; FETC_total {r['FETC_total']}; FETC_mean {fmt(r['FETC_mean'])}\n"
        )

    final += "\n## RQ answers (paper-level, cautious)\n\n"
    final += (
        f"- **RQ1**: Point gates G1–G4: "
        f"G1={'PASS' if g1_point else 'FAIL'}, "
        f"G2={'PASS' if next(g for g in gates if g['gate_id']=='G2_ESR_E_vs_A')['point_estimate_pass'] else 'FAIL'}, "
        f"G3={'PASS' if next(g for g in gates if g['gate_id']=='G3_TPSE_E_vs_D')['point_estimate_pass'] else 'FAIL'}, "
        f"G4={'PASS' if next(g for g in gates if g['gate_id']=='G4_TPAE_E_vs_D')['point_estimate_pass'] else 'FAIL'}. "
        f"CI for ΔESR(E−D) [{fmt(g1['ci_lo'])},{fmt(g1['ci_hi'])}]. "
        + (
            "点估计满足门禁但若 CI 跨过非劣界，仅可写点估计门禁 + 把握度不足。"
            if not g1_ci_ok
            else "G1 点估计与 CI 均不低于 −ε。"
        )
        + " **不得**写成已证非劣。\n"
    )
    final += (
        "- **RQ2**: Task-aware assembly (E vs F/G/H) — see bootstrap ESR deltas; "
        "interpret descriptively with CI width.\n"
    )
    final += (
        "- **RQ3**: VP/vproof — P1 runner uses pre_send checks; "
        "live INSUFFICIENT block not observed in P0/P1 runs; "
        "unit/mock only for block path. VP does not prove semantic equivalence.\n"
    )
    final += (
        "- **RQ4**: Suitable for paper **draft** with limitations; "
        "not for claims of architectural validity or large-model generalization; "
        "related-work novelty not systematically verified.\n"
    )
    final += "\n## Failure attribution\n\n"
    final += f"- Categories: {fail_by_cat}\n- By arm: {fail_by_arm}\n"
    final += "- Detail: failure_attribution.csv\n"
    final += "\n## Reproducibility\n\n"
    final += f"- script: analysis/_run_analysis.py\n- seed={SEED}, B={B_BOOT}\n"

    (ANALYSIS / "final_statistical_report.md").write_text(final, encoding="utf-8")

    # ---------- manifest ----------
    outputs = [
        "data_integrity_report.md",
        "confidence_intervals.csv",
        "bootstrap_results.csv",
        "bootstrap_deltas_sample.csv",
        "failure_attribution.csv",
        "rq_gate_decision.md",
        "final_statistical_report.md",
        "rq_gate_points.csv",
    ]
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "bootstrap_B": B_BOOT,
        "bootstrap_unit": "task_id (all arms, all R per task)",
        "inputs_sha256": {k: sha256(p) for k, p in inputs.items()},
        "outputs_sha256": {},
        "parameters": {
            "eps_vs_D": 0.10,
            "eps_vs_A": 0.15,
            "tpse_threshold": 0.95,
            "tpae_threshold": 1.05,
        },
    }
    for name in outputs:
        p = ANALYSIS / name
        if p.exists():
            manifest["outputs_sha256"][name] = sha256(p)
    (ANALYSIS / "analysis_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("INTEGRITY", json.dumps({k: integrity[k] for k in integrity if k != "tasks"}, ensure_ascii=False))
    print(ci_df.to_string(index=False))
    print(boot_summary.to_string(index=False))
    print("gates", [(g["gate_id"], g["point_estimate_pass"]) for g in gates])
    print("fail", fail_by_cat, "n", len(fail_df))


if __name__ == "__main__":
    main()
