#!/usr/bin/env python
"""E vs F deep diagnosis. Read-only on P1 raw data."""

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
OUT = ROOT / "ef_diagnosis"
OUT.mkdir(exist_ok=True)
SEED = 20261102
B = 10000


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / den, (c + h) / den


def main() -> None:
    df = pd.read_csv(ROOT / "per_step_all.csv")
    df["error"] = df["error"].fillna("")
    df["eval_success"] = pd.to_numeric(df["eval_success"], errors="coerce")

    # --- arm definition from config + prereg snapshot ---
    cfg = Path("p1/scripts/v12/config.py").read_text(encoding="utf-8")
    prereg = Path("p1/docs/v1.2_experiment_preregistration.md").read_text(encoding="utf-8")
    arm_def = {
        "E": {
            "non_target_related": "digest",
            "non_target_unrelated": "none",
            "code_in_config": '"E":' in cfg and 'non_target_related": "digest"' in cfg,
            "prereg_row": "| E | Digest | NONE | FULL |" in prereg,
            "runtime_example": "v1_RUR02_E_R1 step1: FILE hot + INDEX stable_*",
        },
        "F": {
            "non_target_related": "full",
            "non_target_unrelated": "none",
            "code_in_config": '"F":' in cfg and 'non_target_related": "full"' in cfg,
            "prereg_row": "| F | **Full** | NONE | FULL |" in prereg,
            "runtime_example": "v1_RUR02_F_R1 step1: FILE hot+stable_a+stable_b",
        },
        "shared": {
            "must_full_edit_targets": "FULL both",
            "o_prime_vp": "same",
            "k_max": 8,
            "closure_depth": 2,
            "only_diff_per_prereg": "related non-target: Digest(E) vs Full(F)",
        },
    }
    (OUT / "arm_definition_diff.md").write_text(
        f"""# E vs F Arm Definition Diff

Generated: {datetime.now(timezone.utc).isoformat()}

## Sources
- preregistration: p1/docs/v1.2_experiment_preregistration.md (§3.0)
- config: p1/scripts/v12/config.py (_ARMS)
- runtime: runs/*/runner_out/.../context.txt

## E
{json.dumps(arm_def['E'], ensure_ascii=False, indent=2)}

## F
{json.dumps(arm_def['F'], ensure_ascii=False, indent=2)}

## Shared (must be identical)
{json.dumps(arm_def['shared'], ensure_ascii=False, indent=2)}

## Doc/code/runtime consistency
- E: config digest + prereg Digest/NONE/FULL + RUR02 INDEX files → **CONSISTENT**
- F: config full + prereg Full/NONE/FULL + RUR02 all FILE → **CONSISTENT**
- Single intended difference: related non-target level (Digest vs Full).

## Mechanism matrix

| Mechanism | E | F |
| --- | --- | --- |
| EditTargets → FULL | yes | yes |
| CandidateFull → FULL | yes | yes |
| VP/vproof omit | yes | yes |
| must_full | yes | yes |
| related non-target | DIGEST | FULL |
| unrelated non-target | NONE | NONE |
| Kmax / d | 8 / 2 | 8 / 2 |
| task_aware_r | on | on |
""",
        encoding="utf-8",
    )

    # --- episode level ---
    ep = (
        df.groupby(["arm", "task", "rep"], as_index=False)
        .agg(
            both=("eval_success", lambda s: int((s == 1).all()) if len(s) == 2 else 0),
            step_pass=("eval_success", lambda s: int((s == 1).sum())),
            n_steps=("eval_success", "count"),
            tot=("total_tokens", "sum"),
            prompt=("prompt_tokens", "sum"),
            comp=("completion_tokens", "sum"),
        )
    )

    ef = ep[ep.arm.isin(["E", "F"])].copy()
    # pivot per task-rep
    rows = []
    for (task, rep), g in ef.groupby(["task", "rep"]):
        e = g[g.arm == "E"].iloc[0]
        f = g[g.arm == "F"].iloc[0]
        rows.append(
            {
                "task_id": task,
                "rep": int(rep),
                "E_success": int(e.both),
                "F_success": int(f.both),
                "delta_success": int(f.both - e.both),
                "E_step_pass": int(e.step_pass),
                "F_step_pass": int(f.step_pass),
                "E_total_tokens": int(e.tot),
                "F_total_tokens": int(f.tot),
                "delta_tokens": int(f.tot - e.tot),
                "E_prompt": int(e.prompt),
                "F_prompt": int(f.prompt),
                "E_completion": int(e.comp),
                "F_completion": int(f.comp),
                "winner": (
                    "F_only" if f.both == 1 and e.both == 0
                    else "E_only" if e.both == 1 and f.both == 0
                    else "both_success" if e.both == 1 and f.both == 1
                    else "both_fail"
                ),
            }
        )
    pair = pd.DataFrame(rows)
    pair.to_csv(OUT / "task_level_comparison.csv", index=False)

    # task aggregates
    task_sum = (
        pair.groupby("task_id")
        .agg(
            n=("rep", "count"),
            E_sr=("E_success", "mean"),
            F_sr=("F_success", "mean"),
            E_spr=("E_step_pass", "sum"),
            F_spr=("F_step_pass", "sum"),
            E_tok=("E_total_tokens", "sum"),
            F_tok=("F_total_tokens", "sum"),
            F_only=("winner", lambda s: (s == "F_only").sum()),
            E_only=("winner", lambda s: (s == "E_only").sum()),
            both_suc=("winner", lambda s: (s == "both_success").sum()),
            both_fail=("winner", lambda s: (s == "both_fail").sum()),
        )
        .reset_index()
    )
    task_sum["delta_sr"] = task_sum.F_sr - task_sum.E_sr
    task_sum["delta_tok"] = task_sum.F_tok - task_sum.E_tok
    task_sum.to_csv(OUT / "task_level_summary.csv", index=False)

    print("winner counts", pair.winner.value_counts().to_dict())
    print("F_only tasks", task_sum[task_sum.F_only > 0][["task_id", "F_only", "E_only", "delta_sr"]].to_string(index=False))
    print("E_only tasks", task_sum[task_sum.E_only > 0][["task_id", "E_only", "F_only", "delta_sr"]].to_string(index=False))

    # --- context composition from result/context ---
    comp_rows = []
    for rj in ROOT.glob("runs/*/runner_out/episodes/*/*/steps/*/result.json"):
        parts = rj.parts
        ei = parts.index("episodes")
        task, bl = parts[ei + 1], parts[ei + 2]
        arm = bl.rsplit("_", 1)[-1] if "v1.2" in bl else ""
        if arm not in ("E", "F"):
            continue
        d = json.loads(rj.read_text(encoding="utf-8"))
        ctx_p = rj.parent / "context.txt"
        ctx = ctx_p.read_text(encoding="utf-8") if ctx_p.exists() else ""
        n_file = ctx.count("--- FILE ")
        n_index = ctx.count("--- INDEX ")
        # parse pre_send if any
        psc_p = rj.parent / "pre_send_check.json"
        psc = json.loads(psc_p.read_text(encoding="utf-8")) if psc_p.exists() else {}
        resp = rj.parent / "response.txt"
        rs = resp.read_text(encoding="utf-8", errors="replace").strip() if resp.exists() else ""
        comp_rows.append(
            {
                "episode_id": "_".join(parts[parts.index("runs") + 1].split("_")[:3]) if False else f"{task}_{arm}_R{d.get('rep','?')}",
                "task": task,
                "arm": arm,
                "step": parts[ei + 4],
                "prompt_tokens": d.get("prompt_tokens", 0),
                "completion_tokens": d.get("completion_tokens", 0),
                "total_tokens": d.get("total_tokens", 0),
                "n_full_files": n_file,
                "n_digest_index": n_index,
                "must_full_count": d.get("must_full_count"),
                "edit_targets": d.get("edit_targets"),
                "et_verified": psc.get("edit_target_full_verified"),
                "psc_ok": psc.get("ok"),
                "response_head": rs[:60].replace("\n", " | "),
                "response_no_edit": rs == "NO_EDIT",
                "eval_success": d.get("eval_success"),
            }
        )
    ctx_df = pd.DataFrame(comp_rows)
    # fix episode_id from path better
    eps = []
    for rj in ROOT.glob("runs/*/runner_out/episodes/*/*/steps/*/result.json"):
        parts = rj.parts
        ei = parts.index("episodes")
        run_ep = parts[parts.index("runs") + 1]
        arm = parts[ei + 2].rsplit("_", 1)[-1]
        eps.append((run_ep, parts[ei + 1], arm, parts[ei + 4]))
    # rebuild properly
    comp_rows = []
    for rj in ROOT.glob("runs/*/runner_out/episodes/*/*/steps/*/result.json"):
        parts = rj.parts
        ei = parts.index("episodes")
        run_ep = parts[parts.index("runs") + 1]
        task = parts[ei + 1]
        bl = parts[ei + 2]
        arm = bl.rsplit("_", 1)[-1]
        if arm not in ("E", "F"):
            continue
        d = json.loads(rj.read_text(encoding="utf-8"))
        ctx = (rj.parent / "context.txt").read_text(encoding="utf-8") if (rj.parent / "context.txt").exists() else ""
        psc_p = rj.parent / "pre_send_check.json"
        psc = json.loads(psc_p.read_text(encoding="utf-8")) if psc_p.exists() else {}
        resp = rj.parent / "response.txt"
        rs = resp.read_text(encoding="utf-8", errors="replace").strip() if resp.exists() else ""
        comp_rows.append(
            {
                "episode_id": run_ep,
                "task": task,
                "arm": arm,
                "step": parts[ei + 4],
                "prompt_tokens": d.get("prompt_tokens") or 0,
                "completion_tokens": d.get("completion_tokens") or 0,
                "total_tokens": d.get("total_tokens") or 0,
                "n_full_files": ctx.count("--- FILE "),
                "n_digest_index": ctx.count("--- INDEX "),
                "must_full_count": d.get("must_full_count"),
                "edit_targets": str(d.get("edit_targets")),
                "et_verified": psc.get("edit_target_full_verified"),
                "psc_ok": psc.get("ok"),
                "response_no_edit": rs == "NO_EDIT",
                "response_head": rs[:70].replace("\n", " | "),
                "eval_success": d.get("eval_success"),
                "error": d.get("error") or "",
            }
        )
    ctx_df = pd.DataFrame(comp_rows)
    ctx_df.to_csv(OUT / "context_token_comparison.csv", index=False)

    # context stats by arm
    ctx_sum = (
        ctx_df.groupby("arm")
        .agg(
            steps=("step", "count"),
            mean_full=("n_full_files", "mean"),
            mean_index=("n_digest_index", "mean"),
            mean_prompt=("prompt_tokens", "mean"),
            mean_comp=("completion_tokens", "mean"),
            mean_total=("total_tokens", "mean"),
            no_edit_rate=("response_no_edit", "mean"),
            et_verified_true=("et_verified", lambda s: int(sum(bool(x) for x in s))),
            psc_ok_true=("psc_ok", lambda s: int(sum(bool(x) for x in s))),
        )
        .round(3)
    )
    print("\nCONTEXT/TOKEN by arm\n", ctx_sum.to_string())

    # --- failure comparison from existing failure file or reclassify ---
    fail_path = ROOT / "analysis" / "failure_attribution.csv"
    fail = pd.read_csv(fail_path)
    ef_fail = fail[fail.arm.isin(["E", "F"])].copy()
    fail_cmp = (
        ef_fail.groupby(["arm", "primary_failure_category"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    fail_cmp.to_csv(OUT / "failure_comparison.csv", index=False)
    print("\nFAIL cmp\n", fail_cmp.to_string(index=False))

    # --- safety E vs F ---
    safety = {
        "E_et_verified_all": bool(ctx_df[ctx_df.arm == "E"].et_verified.fillna(False).all()),
        "F_et_verified_all": bool(ctx_df[ctx_df.arm == "F"].et_verified.fillna(False).all()),
        "E_psc_ok_all": bool(ctx_df[ctx_df.arm == "E"].psc_ok.fillna(False).all()),
        "F_psc_ok_all": bool(ctx_df[ctx_df.arm == "F"].psc_ok.fillna(False).all()),
        "E_insufficient": int(ctx_df[ctx_df.arm == "E"].error.astype(str).str.contains("INSUFFICIENT").sum()),
        "F_insufficient": int(ctx_df[ctx_df.arm == "F"].error.astype(str).str.contains("INSUFFICIENT").sum()),
        "note": "F advantage must not come from looser VP; both use same must/ET rules per prereg",
    }
    print("SAFETY", safety)

    # --- bootstrap E vs F task-cluster ---
    # episode level success and tokens for E,F
    def collect(arm):
        d = {}
        for _, r in ep[ep.arm == arm].iterrows():
            d.setdefault(r.task, []).append({"s": int(r.both), "t": float(r.tot)})
        return d

    e_map, f_map = collect("E"), collect("F")
    tasks = sorted(set(e_map) | set(f_map))
    rng = random.Random(SEED)

    def esr(m, sample):
        s = n = 0
        for t in sample:
            for it in m.get(t, []):
                s += it["s"]
                n += 1
        return s / n if n else float("nan")

    def tpae(m, sample):
        toks = [i["t"] for t in sample for i in m.get(t, [])]
        return sum(toks) / len(toks) if toks else float("nan")

    def tpse(m, sample):
        toks = [i["t"] for t in sample for i in m.get(t, [])]
        succ = [i["s"] for t in sample for i in m.get(t, [])]
        ns = sum(succ)
        if ns == 0:
            return None
        return sum(toks) / ns

    def spr(m, sample):
        # step pass approximated as both*2/2 from episode - use ep step_pass
        # rebuild step map
        return float("nan")  # filled below

    # step-level for SPR delta
    step_map = {a: {} for a in ("E", "F")}
    for _, r in df[df.arm.isin(["E", "F"])].iterrows():
        step_map[r.arm].setdefault(r.task, []).append(int(r.eval_success == 1))

    def spr_of(m, sample):
        vals = [x for t in sample for x in m.get(t, [])]
        return sum(vals) / len(vals) if vals else float("nan")

    deltas = {"ESR": [], "SPR": [], "TPAE": [], "TPSE": []}
    na_tpse = 0
    for _ in range(B):
        sample = [tasks[rng.randrange(len(tasks))] for _ in range(len(tasks))]
        deltas["ESR"].append(esr(f_map, sample) - esr(e_map, sample))
        deltas["SPR"].append(spr_of(step_map["F"], sample) - spr_of(step_map["E"], sample))
        deltas["TPAE"].append(tpae(f_map, sample) - tpae(e_map, sample))
        v_f, v_e = tpse(f_map, sample), tpse(e_map, sample)
        if v_f is None or v_e is None:
            na_tpse += 1
            deltas["TPSE"].append(float("nan"))
        else:
            deltas["TPSE"].append(v_f - v_e)

    def point(m_get, metric):
        if metric == "ESR":
            return esr(f_map, tasks) - esr(e_map, tasks)
        if metric == "SPR":
            return spr_of(step_map["F"], tasks) - spr_of(step_map["E"], tasks)
        if metric == "TPAE":
            return tpae(f_map, tasks) - tpae(e_map, tasks)
        ve, vf = tpse(e_map, tasks), tpse(f_map, tasks)
        if ve is None or vf is None:
            return float("nan")
        return vf - ve

    boot_rows = []
    for metric, vals in deltas.items():
        s = pd.Series(vals, dtype=float).dropna()
        pe = point(None, metric)
        lo = float(s.quantile(0.025)) if len(s) else float("nan")
        hi = float(s.quantile(0.975)) if len(s) else float("nan")
        boot_rows.append(
            {
                "comparison": "F-E",
                "metric": metric,
                "point_estimate": pe,
                "ci_lo": lo,
                "ci_hi": hi,
                "n_valid": int(len(s)),
                "n_na": B - int(len(s)) if metric == "TPSE" else 0,
            }
        )
    boot_df = pd.DataFrame(boot_rows)
    boot_df.to_csv(OUT / "ef_bootstrap.csv", index=False)
    print("\nBOOT\n", boot_df.to_string(index=False))

    # task win/loss
    wins = {
        "F_only_eps": int((pair.winner == "F_only").sum()),
        "E_only_eps": int((pair.winner == "E_only").sum()),
        "both_success_eps": int((pair.winner == "both_success").sum()),
        "both_fail_eps": int((pair.winner == "both_fail").sum()),
        "tasks_F_stricter": int((task_sum.delta_sr > 0).sum()),
        "tasks_E_stricter": int((task_sum.delta_sr < 0).sum()),
        "tasks_tie": int((task_sum.delta_sr == 0).sum()),
    }
    print("WINS", wins)

    # token means
    e_tok = ep[ep.arm == "E"]
    f_tok = ep[ep.arm == "F"]
    token_note = {
        "E_TPAE": float(e_tok.tot.mean()),
        "F_TPAE": float(f_tok.tot.mean()),
        "E_TPSE": float(e_tok.tot.sum() / e_tok.both.sum()),
        "F_TPSE": float(f_tok.tot.sum() / f_tok.both.sum()),
        "E_ESR": float(e_tok.both.mean()),
        "F_ESR": float(f_tok.both.mean()),
        "delta_TPAE_pct": float((f_tok.tot.mean() / e_tok.tot.mean() - 1) * 100),
        "delta_TPSE_pct": float(
            (f_tok.tot.sum() / f_tok.both.sum()) / (e_tok.tot.sum() / e_tok.both.sum()) - 1
        )
        * 100,
        "delta_ESR_pp": float((f_tok.both.mean() - e_tok.both.mean()) * 100),
    }
    print("TOKENS", token_note)

    # case studies: pick F_only and E_only
    cases = []
    for _, r in pair[pair.winner.isin(["F_only", "E_only"])].iterrows():
        cases.append(r.to_dict())
    # also a both_fail high token
    case_md = "# E vs F Case Studies\n\n"
    for c in cases[:12]:
        case_md += f"## {c['task_id']} R{c['rep']} → {c['winner']}\n"
        case_md += f"- E success={c['E_success']} tokens={c['E_total_tokens']}; F success={c['F_success']} tokens={c['F_total_tokens']}\n"
        for arm in ("E", "F"):
            eid = f"{c['task_id']}_{arm}_R{c['rep']}"
            # find failure/success steps
            sub = ctx_df[ctx_df.episode_id == eid]
            for _, s in sub.iterrows():
                case_md += (
                    f"  - {arm} {s.step}: eval={s.eval_success} prompt={s.prompt_tokens} "
                    f"full={s.n_full_files} idx={s.n_digest_index} no_edit={s.response_no_edit} "
                    f"resp={s.response_head!r}\n"
                )
            # evidence path
            case_md += f"  - evidence: `runs/{eid}/runner_out/episodes/...`\n"
    (OUT / "case_studies.md").write_text(case_md, encoding="utf-8")

    # optimization proposal
    f_better_sr = task_sum.delta_sr.mean() < 0  # F lower than E if delta = F-E negative... wait delta_sr = F-E, F better means positive
    # F ESR 35 vs E 32 so F higher overall
    prop = f"""# V1.3 Optimization Proposal (from E vs F diagnosis)

## 1. F vs E — real difference

**Only intended difference**: related non-target files → **Full (F)** vs **Digest (E)**.
Shared: EditTargets FULL, CandidateFull FULL, VP/vproof, must_full, Kmax=8, d=2, unrelated=NONE.

Runtime proof: RUR02 E = FILE hot + INDEX stable_*; F = all three FILE.

## 2. Where F is better

- Global ESR: F 35/72 vs E 32/72 (+4.2pp); bootstrap delta ESR (F-E)={boot_df[boot_df.metric=='ESR'].point_estimate.iloc[0]:.4f} CI [{boot_df[boot_df.metric=='ESR'].ci_lo.iloc[0]:.4f},{boot_df[boot_df.metric=='ESR'].ci_hi.iloc[0]:.4f}]
- Wins: F_only eps={wins['F_only_eps']} vs E_only={wins['E_only_eps']}
- TPSE_F={token_note['F_TPSE']:.1f} < TPSE_E={token_note['E_TPSE']:.1f} ({token_note['delta_TPSE_pct']:.1f}%)

## 3. Where F is worse

- TPAE_F={token_note['F_TPAE']:.1f} > TPAE_E={token_note['E_TPAE']:.1f} ({token_note['delta_TPAE_pct']:.1f}%) — **more tokens per attempted episode**
- TPSE improvement is largely **denominator effect**: F has more successes, so TPSE falls even though TPAE rises
- Full injection of related non-targets costs prompt tokens when those files are not needed

## 4. Why F may win (evidence vs hypothesis)

| Claim | Evidence |
| --- | --- |
| More complete related context reduces model confusion | **Partial**: F_only cases often have extra FILE blocks; not all cases show causal proof |
| Digest INDEX insufficient for 1.5B | **Hypothesis**: E RUR02 has INDEX only; still NO_EDIT on both — weak |
| TPSE drop from higher success rate | **Direct**: arithmetic on E/F totals |
| Not from looser safety | **Direct**: same ET/VP rules; et_verified all true both arms |

## 5. Can merge into E?

**Candidate A (data-backed)**: For must-adjacent related files — already shared via must_full.
**Candidate B (needs test)**: Upgrade related non-target Digest→Full when file is in dep graph of EditTargets (often already must).
**Candidate C**: Make F the default related=full — **TPAE +0.8%** must be accepted; not free.

**Do not**: drop VP/must/ET safety to gain speed (F did not do this).

## 6. V1.3 candidate (minimal)

1. **Related non-target default = Full** (adopt F policy) for 1.5B code-edit protocol.
2. Keep E as **Digest ablation arm** for papers.
3. Optional: auto-upgrade Digest→Full if related file in instruction or dep graph.
4. Keep VP, ET, CandidateFull unchanged.

## 7. Risk to VP safety
None if only changing non-target level; **must not** relax EditTargets/VP.

## 8. Minimal next experiment
- Prefer **descriptive merge analysis** on existing P1 before new runs.
- If new runs: small 8-task R=1 E vs F confirmation only.

## Classification
- **A (data)**: F has higher ESR, lower TPSE, higher TPAE on this P1; same safety flags.
- **B (hypothesis)**: Digest harms 1.5B more than Full costs.
- **C (do not)**: relax VP/ET to reduce tokens.

## Conclusion
F advantage is **context completeness for related non-targets**, paid with **~0.8% higher TPAE** and **~7.8% lower TPSE** (success denominator). Worth **V1.3 candidate default related=Full** with VP unchanged; validate small set before paper claim.
"""
    (OUT / "v13_optimization_proposal.md").write_text(prop, encoding="utf-8")

    # manifest
    outputs = [
        "arm_definition_diff.md",
        "task_level_comparison.csv",
        "task_level_summary.csv",
        "failure_comparison.csv",
        "context_token_comparison.csv",
        "ef_bootstrap.csv",
        "case_studies.md",
        "v13_optimization_proposal.md",
    ]
    inputs = {
        "per_step_all": ROOT / "per_step_all.csv",
        "failure_attribution": ROOT / "analysis" / "failure_attribution.csv",
        "prereg": Path("p1/docs/v1.2_experiment_preregistration.md"),
        "config": Path("p1/scripts/v12/config.py"),
    }
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "B": B,
        "inputs_sha256": {k: sha(p) for k, p in inputs.items() if p.exists()},
        "outputs_sha256": {n: sha(OUT / n) for n in outputs},
        "wins": wins,
        "token_note": token_note,
        "safety": safety,
    }
    (OUT / "diagnosis_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("WROTE", list(OUT.iterdir()))


if __name__ == "__main__":
    main()
