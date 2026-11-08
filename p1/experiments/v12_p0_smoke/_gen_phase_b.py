#!/usr/bin/env python
"""Phase B: generate P0 execution planning artifacts (no model calls)."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path("p1/experiments/v12_p0_smoke")
TASKS = [
    "v1_IRR01",
    "v1_CFD01",
    "v1_DUP01",
    "v1_DEL01",
    "v1_RUR02",
    "v1_RFS01",
    "v1_RUR03",
    "v1_STM02",
]
ARMS = ["E", "F", "G", "H"]
REP = 1
SEED = 20261102


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snapshot_info(task_id: str) -> dict:
    proj = Path("p1/tasks") / task_id / "project"
    files = {}
    for f in sorted(proj.rglob("*")):
        if f.is_file():
            files[f.relative_to(proj).as_posix()] = sha256_file(f)
    blob = json.dumps(files, sort_keys=True).encode()
    return {
        "source": f"p1/tasks/{task_id}/project",
        "file_count": len(files),
        "file_hashes": files,
        "snapshot_sha256": hashlib.sha256(blob).hexdigest(),
    }


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    meta = json.loads(Path("p1/tasks/tasks_v1.0.json").read_text(encoding="utf-8"))
    by = {e["id"]: e for e in meta["episodes"]}
    for t in TASKS:
        if t not in by:
            raise SystemExit(f"missing task {t}")

    original = [
        {"episode_id": f"{t}_{a}_R{REP}", "task_id": t, "arm": a, "repetition": REP}
        for t in TASKS
        for a in ARMS
    ]
    rng = random.Random(SEED)
    order = list(original)
    rng.shuffle(order)

    episodes = []
    for i, ep in enumerate(order, 1):
        snap = snapshot_info(ep["task_id"])
        episodes.append(
            {
                **ep,
                "planned_order": i,
                "expected_steps": len(by[ep["task_id"]]["steps"]),
                "initial_workspace_snapshot": snap["source"],
                "initial_workspace_hash": snap["snapshot_sha256"],
                "initial_workspace_file_count": snap["file_count"],
                "status": "PLANNED",
                "isolation": "fresh_copy_from_snapshot_per_episode",
            }
        )

    ids = [e["episode_id"] for e in episodes]
    if len(episodes) != 32 or len(set(ids)) != 32:
        raise SystemExit("episode count/uniqueness failed")

    episode_manifest = {
        "schema": "v12-p0-episode-manifest-v1",
        "seed_reference": SEED,
        "episode_count": 32,
        "tasks": TASKS,
        "arms": ARMS,
        "repetition": REP,
        "episodes": episodes,
        "isolation_rule": (
            "Each episode: copytree from frozen project snapshot; no cross-episode "
            "workspace reuse; step2 uses only that episode's step1 workspace state."
        ),
        "request_upper_bound": 64,
        "request_upper_bound_note": (
            "64=32*2 theoretical max, not required completions; INSUFFICIENT may reduce calls."
        ),
    }
    (ROOT / "episode_manifest.json").write_text(
        json.dumps(episode_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rand_manifest = {
        "schema": "v12-p0-randomization-v1",
        "random_seed": SEED,
        "randomization_method": "python random.Random(seed).shuffle",
        "original_episode_order": [e["episode_id"] for e in original],
        "randomized_episode_order": ids,
        "episode_count": 32,
        "uniqueness_check": {
            "all_unique": True,
            "count": len(set(ids)),
            "duplicates": [k for k, v in Counter(ids).items() if v > 1],
            "missing_from_original": sorted(
                set(e["episode_id"] for e in original) - set(ids)
            ),
            "extra": sorted(set(ids) - set(e["episode_id"] for e in original)),
        },
    }
    (ROOT / "randomization_manifest.json").write_text(
        json.dumps(rand_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rows = [
        {
            "task_id": "v1_IRR01",
            "source_file": "p1/tasks/tasks_v1.0.json",
            "task_description": "step1 alpha.py a()=10; step2 add a2(); do not modify beta.py",
            "original_step_count": 2,
            "target_mechanisms": "edit_target;negative_intent;file_overwrite;O_prime",
            "expected_trigger": "EXPECTED_TRIGGER:EditTargets_FULL;EXPECTED_TRIGGER:negative_Excluded;EXPECTED_TRIGGER:no_omit_edit_target",
            "not_expected": "NOT_EXPECTED:digest_as_full_source",
            "uncertain": "UNCERTAIN:CandidateFull",
            "validation_focus": "alpha FULL in current context step2; beta not EditTarget",
            "notes": "focus=irrelevant_change; files=alpha.py,beta.py",
        },
        {
            "task_id": "v1_CFD01",
            "source_file": "p1/tasks/tasks_v1.0.json",
            "task_description": "step1 tax.py rate; step2 invoice.py net_total uses tax_rate",
            "original_step_count": 2,
            "target_mechanisms": "cross_file_dep;dep_closure;edit_target;must_full",
            "expected_trigger": "EXPECTED_TRIGGER:dep_closure_must_full;EXPECTED_TRIGGER:multi_file_FULL",
            "not_expected": "NOT_EXPECTED:negative_intent",
            "uncertain": "UNCERTAIN:O_prime_non_target_step2",
            "validation_focus": "dependency FULL injection",
            "notes": "focus=cross_file_dep",
        },
        {
            "task_id": "v1_DUP01",
            "source_file": "p1/tasks/tasks_v1.0.json",
            "task_description": "step1 mathx.norm=x/4 do not change textx; step2 textx norm2",
            "original_step_count": 2,
            "target_mechanisms": "disambiguation;negative_intent;edit_target",
            "expected_trigger": "EXPECTED_TRIGGER:negative_textx_step1;EXPECTED_TRIGGER:edit_target",
            "not_expected": "NOT_EXPECTED:forced_omit_mathx",
            "uncertain": "UNCERTAIN:partial_success",
            "validation_focus": "disambiguation dual-file safety",
            "notes": "focus=disambiguation",
        },
        {
            "task_id": "v1_DEL01",
            "source_file": "p1/tasks/tasks_v1.0.json",
            "task_description": "step1 delete lib.dead; step2 app twice_keep",
            "original_step_count": 2,
            "target_mechanisms": "tombstone;state_change;edit_target",
            "expected_trigger": "EXPECTED_TRIGGER:tombstone;EXPECTED_TRIGGER:edit_target_app_step2",
            "not_expected": "NOT_EXPECTED:drop_edit_target_full",
            "uncertain": "UNCERTAIN:O_prime_lib_step2",
            "validation_focus": "delete then edit injection",
            "notes": "focus=delete_tombstone",
        },
        {
            "task_id": "v1_RUR02",
            "source_file": "p1/tasks/tasks_v1.0.json",
            "task_description": "hot()=2/3; do not modify stable_a/stable_b",
            "original_step_count": 2,
            "target_mechanisms": "context_selection;negative_intent;O_prime",
            "expected_trigger": "EXPECTED_TRIGGER:hot_EditTarget_FULL;EXPECTED_TRIGGER:stable_not_EditTarget",
            "not_expected": "NOT_EXPECTED:stable_as_EditTarget",
            "uncertain": "UNCERTAIN:digest_on_stable_E",
            "validation_focus": "non-target policy E/F/G/H",
            "notes": "focus=safe_omission",
        },
        {
            "task_id": "v1_RFS01",
            "source_file": "p1/tasks/tasks_v1.0.json",
            "task_description": "mode describe active; app is_active",
            "original_step_count": 2,
            "target_mechanisms": "history_state;edit_target;cross_file",
            "expected_trigger": "EXPECTED_TRIGGER:mode_step1;EXPECTED_TRIGGER:app_step2",
            "not_expected": "NOT_EXPECTED:unsafe_omit_mode",
            "uncertain": "UNCERTAIN:O_prime_after_step1",
            "validation_focus": "state after refresh; step2 injection",
            "notes": "focus=refresh_control",
        },
        {
            "task_id": "v1_RUR03",
            "source_file": "p1/tasks/tasks_v1.0.json",
            "task_description": "c1()=10; adjust c1/c3 behavior",
            "original_step_count": 2,
            "target_mechanisms": "model_capability;edit_target",
            "expected_trigger": "EXPECTED_TRIGGER:edit_target_core",
            "not_expected": "NOT_EXPECTED:blame_architecture_for_NO_EDIT_alone",
            "uncertain": "UNCERTAIN:model_protocol_NO_EDIT",
            "validation_focus": "model boundary; injection still correct",
            "notes": "focus=mixed_local",
        },
        {
            "task_id": "v1_STM02",
            "source_file": "p1/tasks/tasks_v1.0.json",
            "task_description": "fee service=qty*6; bill due_fast hardcoded",
            "original_step_count": 2,
            "target_mechanisms": "reasoning_control;edit_target;multi_file",
            "expected_trigger": "EXPECTED_TRIGGER:fee_step1;EXPECTED_TRIGGER:bill_step2",
            "not_expected": "NOT_EXPECTED:arith_error_as_memory_bug",
            "uncertain": "UNCERTAIN:model_arithmetic_error",
            "validation_focus": "injection vs reasoning separation",
            "notes": "focus=stale_summary",
        },
    ]
    with (ROOT / "task_mapping.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("OK episodes", len(episodes), "seed", SEED)
    print("order_head", ids[:5])


if __name__ == "__main__":
    main()
