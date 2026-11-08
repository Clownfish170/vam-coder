#!/usr/bin/env python
"""Read-only P0 post-execution review computations. Writes post_review CSVs only."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("p1/experiments/v12_p0_smoke")
EXEC = ROOT / "execution"
POST = ROOT / "post_review"
POST.mkdir(parents=True, exist_ok=True)


def sha(p: str) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> None:
    summary = pd.read_csv(EXEC / "summary.csv")
    per = pd.read_csv(EXEC / "per_step_all.csv")
    em = json.loads((ROOT / "episode_manifest.json").read_text(encoding="utf-8"))
    order = json.loads((EXEC / "execution_order.json" / "log.json").read_text(encoding="utf-8"))

    per = per.copy()
    per["episode_id"] = per["task"] + "_" + per["arm"] + "_R1"

    expected = {e["episode_id"] for e in em["episodes"]}
    observed = set(per["episode_id"])
    step_counts = per.groupby(["arm", "task"]).size()

    integrity = {
        "planned_episodes": em["episode_count"],
        "observed_episodes": len(observed),
        "missing": sorted(expected - observed),
        "extra": sorted(observed - expected),
        "episodes_not_2_steps": int((step_counts != 2).sum()),
        "arm_episode_counts": per.groupby("arm")["task"].nunique().to_dict(),
        "prompt_gt_zero": int((per["prompt_tokens"] > 0).sum()),
        "prompt_eq_zero": int((per["prompt_tokens"] == 0).sum()),
        "nan_cells": int(per.isna().sum().sum()),
        "inf_cells": int(np.isinf(per.select_dtypes("number")).sum().sum()),
        "order_log_n": len(order),
        "order_completed": sum(1 for x in order if x.get("status") == "COMPLETED"),
        "sum_model_requests_log": sum(x.get("model_requests", 0) for x in order),
    }
    print("INTEGRITY", json.dumps(integrity, ensure_ascii=False))

    claimed = {
        "E": dict(ESR="4/8", SPR="9/16", TPAE=539.4, TPSE=1078.8, FETC_total=2026, FETC_mean=506.5),
        "F": dict(ESR="3/8", SPR="8/16", TPAE=542.1, TPSE=1445.7, FETC_total=2599, FETC_mean=519.8),
        "G": dict(ESR="4/8", SPR="9/16", TPAE=556.5, TPSE=1113.0, FETC_total=2089, FETC_mean=522.2),
        "H": dict(ESR="4/8", SPR="9/16", TPAE=542.5, TPSE=1085.0, FETC_total=2013, FETC_mean=503.2),
    }
    rows = []
    for arm in "EFGH":
        sub = per[per.arm == arm]
        g = (
            sub.groupby("task")
            .agg(both=("eval_success", lambda s: int((s == 1).all())), tot=("total_tokens", "sum"))
            .reset_index()
        )
        fail = g[g.both == 0]
        ns = int(g.both.sum())
        n = len(g)
        spr_n = int((sub["eval_success"] == 1).sum())
        rec = {
            "arm": arm,
            "recalc_ESR": f"{ns}/{n}",
            "recalc_SPR": f"{spr_n}/{len(sub)}",
            "recalc_TPAE": round(g.tot.mean(), 1),
            "recalc_TPSE": round(g.tot.sum() / ns, 1) if ns else "NA/inf",
            "recalc_FETC_total": int(fail.tot.sum()) if len(fail) else 0,
            "recalc_FETC_mean": round(fail.tot.mean(), 1) if len(fail) else "NA",
            "claim_ESR": claimed[arm]["ESR"],
            "claim_SPR": claimed[arm]["SPR"],
            "claim_TPAE": claimed[arm]["TPAE"],
            "claim_TPSE": claimed[arm]["TPSE"],
            "claim_FETC_total": claimed[arm]["FETC_total"],
            "claim_FETC_mean": claimed[arm]["FETC_mean"],
        }
        rec["ESR_match"] = rec["recalc_ESR"] == rec["claim_ESR"]
        rec["SPR_match"] = rec["recalc_SPR"] == rec["claim_SPR"]
        rec["TPAE_match"] = abs(float(rec["recalc_TPAE"]) - float(rec["claim_TPAE"])) < 0.15
        rec["TPSE_match"] = abs(float(rec["recalc_TPSE"]) - float(rec["claim_TPSE"])) < 0.15
        rec["FETC_match"] = rec["recalc_FETC_total"] == rec["claim_FETC_total"] and abs(
            float(rec["recalc_FETC_mean"]) - float(rec["claim_FETC_mean"])
        ) < 0.15
        rows.append(rec)
        print(arm, rec)
    pd.DataFrame(rows).to_csv(POST / "metric_recalculation.csv", index=False)

    # Safety audit per step
    safety = []
    for rj in sorted(EXEC.rglob("episodes/*/*/steps/*/result.json")):
        parts = rj.parts
        ei = parts.index("episodes")
        task, bl, step = parts[ei + 1], parts[ei + 2], parts[ei + 4]
        arm = bl.rsplit("_", 1)[-1] if "v1.2" in bl else bl
        res = json.loads(rj.read_text(encoding="utf-8"))
        psc_p = rj.parent / "pre_send_check.json"
        psc = json.loads(psc_p.read_text()) if psc_p.exists() else {}
        ctx = (rj.parent / "context.txt").read_text(encoding="utf-8") if (rj.parent / "context.txt").exists() else ""
        msgs = (
            json.loads((rj.parent / "messages.json").read_text(encoding="utf-8"))
            if (rj.parent / "messages.json").exists()
            else []
        )
        user = [m for m in msgs if m.get("role") == "user"]
        user_ctx = user[-1].get("content", "") if user else ""
        et_list = [x for x in str(res.get("edit_targets") or "").split(";") if x]
        ctx_paths = re.findall(r"--- FILE ([^\s(]+)", ctx)
        et_ok = True
        for p in et_list:
            if not (any(p in line for line in ctx_paths) or f"FILE {p}" in ctx or f"FILE {p}" in user_ctx):
                et_ok = False
        safety.append(
            {
                "episode": f"{task}_{arm}_R1",
                "task": task,
                "arm": arm,
                "step": step,
                "edit_targets": ";".join(et_list),
                "et_full_in_current_ctx": et_ok,
                "n_full_files": len(ctx_paths),
                "n_digest_index": len(re.findall(r"--- INDEX", ctx)),
                "psc_ok": psc.get("ok"),
                "et_verified": psc.get("edit_target_full_verified"),
                "cf_verified": psc.get("candidate_full_verified"),
                "omitted_after": json.dumps(psc.get("omitted_after"), ensure_ascii=False),
                "error": res.get("error"),
                "eval_success": res.get("eval_success"),
                "prompt_tokens": res.get("prompt_tokens"),
                "insufficient": res.get("insufficient"),
            }
        )
    sdf = pd.DataFrame(safety)
    sdf.to_csv(POST / "safety_audit.csv", index=False)
    print(
        "SAFETY et_ok",
        bool(sdf.et_full_in_current_ctx.all()),
        "psc_ok",
        sdf.psc_ok.value_counts(dropna=False).to_dict(),
        "et_verified",
        sdf.et_verified.value_counts(dropna=False).to_dict(),
    )

    # Strategy RUR02 step1
    print("STRATEGY RUR02")
    for arm in "EFGH":
        p = EXEC / f"episodes/v1_RUR02/vam_coder_v1.2_{arm}/steps/step1/context.txt"
        if p.exists():
            lines = [
                ln
                for ln in p.read_text(encoding="utf-8").splitlines()
                if ln.startswith("--- FILE") or ln.startswith("--- INDEX")
            ]
            print(arm, lines)

    # Workspaces
    ws = list(EXEC.rglob("episodes/*/*/workspace"))
    print("workspaces", len(ws))
    frozen = Path("p1/tasks/v1_IRR01/project")
    print(
        "frozen IRR01",
        sorted(x.name for x in frozen.rglob("*.py")),
    )

    # Git
    print("branch", subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip())
    print("head", subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
    print("stash", subprocess.check_output(["git", "stash", "list"], text=True).splitlines()[0])
    expect = {
        "p1/tasks/tasks_v1.0.json": "1f3db0090fd62c8f934ed1271b28d0f955c9763fe2956efb30d2a12179f00339",
        "p1/results/p2_input/formal_runs.csv": "279d80f8c2a4f9e608395bf891ba91541517193dc7548e9e57dae8bacf9c2375",
        "p1/manifests/p1_v1.0_manifest_20261030.json": "e82072f4c222e9927762b383a1e344bcd799d5f08c38486665d7eed8cca696df",
        "p1/docs/v1.2_architecture_design.md": "594a9933df464c8ee91ea2963ff2ede907bc4fd1ab4af08368736be07c6188eb",
        "p1/docs/v1.2_method_formulation.md": "f52bc5bdfd68af11abba256193cd6681137ff536f67362920d9dc3450af24e4f",
        "p1/docs/v1.2_experiment_preregistration.md": "7d594e1c2b5de063ef75c2bdbaa65e5365607c1651a873b2960fc9b70a7425fc",
        "p1/docs/v1.2_implementation_roadmap.md": "579ec72dea4fcecd0dbe47f1d55cc8ab973e7d0c8ba2fb3772fdb51d77fa11d5",
        "p1/docs/v1.2_novelty_and_related_work.md": "95dbfc36e3f2df4fae358986090b79fcb7885f00800cf1eb1343b3a199331be3",
        "p1/docs/v1.2_design_review_response.md": "f0abd2f6eb184ccae6815974b52b81141b2a93375dfcbd4fbcbc890c540e06e6",
        "p1/docs/v1.2_r2.2_change_note.md": "fbcba7ccbcc2dbf701a6abbaa3e8978997259602a6e2ce96e557674d834a3a12",
    }
    all_ok = True
    for p, h in expect.items():
        ok = sha(p) == h
        all_ok = all_ok and ok
        print(("OK" if ok else "DIFF"), p)

    # Failure analysis skeleton
    fails = per[per.eval_success == 0]
    print("failed steps", len(fails))
    fail_rows = []
    for _, r in fails.iterrows():
        ep = f"{r.task}_{r.arm}_R1"
        step = r.step
        base = EXEC / "episodes" / r.task / f"vam_coder_v1.2_{r.arm}" / "steps" / step
        resp = (base / "response.txt").read_text(encoding="utf-8") if (base / "response.txt").exists() else ""
        eval_out = (base / "eval_output.txt").read_text(encoding="utf-8") if (base / "eval_output.txt").exists() else ""
        ctx = (base / "context.txt").read_text(encoding="utf-8") if (base / "context.txt").exists() else ""
        psc = json.loads((base / "pre_send_check.json").read_text()) if (base / "pre_send_check.json").exists() else {}
        applied = json.loads((base / "apply.json").read_text()) if (base / "apply.json").exists() else {}
        resp_s = resp.strip()
        if resp_s == "NO_EDIT":
            primary = "MODEL_NO_EDIT"
        elif "NameError" in eval_out or "assert" in eval_out:
            primary = "MODEL_REASONING_ERROR"
        elif not psc.get("ok", True):
            primary = "VP_VERIFICATION_ERROR"
        elif r.insufficient:
            primary = "CONTEXT_MISSING"
        else:
            primary = "UNDETERMINED"
        # refine NO_EDIT with context check
        if resp_s == "NO_EDIT":
            if "--- FILE" not in ctx:
                primary = "CONTEXT_MISSING"
            else:
                primary = "MODEL_NO_EDIT"
        fail_rows.append(
            {
                "episode_id": ep,
                "task_id": r.task,
                "arm": r.arm,
                "step": step,
                "primary_failure_category": primary,
                "expected": "per tasks_v1.0 step eval",
                "actual_eval": r.eval_success,
                "model_response_head": resp_s[:80].replace("\n", " | "),
                "applied_files": json.dumps(applied.get("applied") if isinstance(applied, dict) else applied),
                "context_has_file": "--- FILE" in ctx,
                "et_verified": psc.get("edit_target_full_verified"),
                "psc_ok": psc.get("ok"),
                "prompt_tokens": r.prompt_tokens,
                "eval_output_head": eval_out[:120].replace("\n", " | "),
                "evidence_path": str(base),
            }
        )
    pd.DataFrame(fail_rows).to_csv(POST / "failure_analysis.csv", index=False)
    print(Counter(f["primary_failure_category"] for f in fail_rows))

    # IRR01
    alpha_p = EXEC / "episodes/v1_IRR01/vam_coder_v1.2_E/workspace/alpha.py"
    if alpha_p.exists():
        print("IRR01 alpha:\n", alpha_p.read_text(encoding="utf-8"))

    # write integrity json
    (POST / "metric_recalculation_integrity.json").write_text(
        json.dumps(integrity, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    from collections import Counter  # noqa: E402

    main()
