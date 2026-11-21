#!/usr/bin/env python
"""independent-v1 任务集生成与冻结（Part2 收口）。

顺序：注册三族 → 配额断言 → 全量校验（validation.validate_all：判别性/目标/
跨集哈希与指令/禁词/信息点平衡）→ 物化磁盘树 → 写 independent_tasks.json →
最后写 manifest（manifest 存在 = 冻结，拒绝重生成）。

prereg sha 在冻结时钉入（P1 同款流程：预注册先冻结，任务集回填其 sha）。
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from validation import (  # noqa: E402
    apply_ops, ref_files, validate_all, write_tree,
)

PREREG_SHA256 = "7023da82be3fb9892434ca183749a8bd6b854f660842e8e809836d3baf495a33"
DESIGN_SHA256 = "d757993d235193cae470c9d172dee13293e13640f9007a7010a1e52af666bb91"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    if (HERE / "independent_tasks_manifest.json").exists():
        print("independent_tasks_manifest.json exists (freeze-once). Refusing.",
              file=sys.stderr)
        return 2

    # 注册
    import families_short  # noqa: F401
    import families_medium  # noqa: F401
    import families_long  # noqa: F401
    from registry import TASKS

    ids = [t["id"] for t in TASKS]
    assert len(ids) == 48, f"expected 48 tasks, got {len(ids)}"
    assert len(set(ids)) == 48, "duplicate task ids"
    diff = [t["difficulty"] for t in TASKS]
    for d, n in (("short", 16), ("medium", 16), ("long", 16)):
        assert diff.count(d) == n, f"{d}: {diff.count(d)} != {n}"
    steps_by_diff = {"short": 2, "medium": 5, "long": 10}
    for t in TASKS:
        assert len(t["steps"]) == steps_by_diff[t["difficulty"]], (
            f"{t['id']}: {len(t['steps'])} steps != {steps_by_diff[t['difficulty']]}"
        )
    fams = sorted({t["family"] for t in TASKS})
    assert len(fams) == 24, f"expected 24 archetypes, got {len(fams)}: {fams}"

    # 全量校验（含跨集与禁词）
    validation = validate_all(TASKS)

    frozen_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    episodes = []
    for t in TASKS:
        episodes.append({
            "id": t["id"],
            "type": t["type"],
            "family": t["family"],
            "difficulty": t["difficulty"],
            "focus": t["focus"],
            "steps": [
                {"id": f"step{i}", "instruction": s["instruction"],
                 "eval": f"eval/step{i}"}
                for i, s in enumerate(t["steps"], 1)
            ],
            "required_info_points": t["info_points"],
        })
    tasks_doc = {
        "task_set_version": "independent-v1",
        "frozen_at": frozen_at,
        "prereg": "p1/docs/v12f_independent_validation_preregistration.md",
        "prereg_sha256": PREREG_SHA256,
        "design": "p1/docs/independent_taskset_design.md",
        "design_sha256": DESIGN_SHA256,
        "quota": {"short": 16, "medium": 16, "long": 16},
        "steps_per_difficulty": steps_by_diff,
        "architectures": ["vam_coder_v1.2_F", "memory_off", "symbol_full_read"],
        "R": 5,
        "randomization_seed_planned": 20261111,
        "frozen_rules": {
            "max_tokens": 2048,
            "bootstrap_seed": 20261102,
            "temperature": 0.0,
            "seed": 0,
            "history_policy": "keep",
        },
        "episodes": episodes,
    }
    tasks_path = HERE / "independent_tasks.json"
    tasks_path.write_text(
        json.dumps(tasks_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tasks_sha = _sha(tasks_path.read_bytes())

    # 物化磁盘树（project / eval / reference）
    for t in TASKS:
        tid = t["id"]
        write_tree(t["files"], HERE / tid / "project")
        for i, step in enumerate(t["steps"], 1):
            ev = HERE / tid / "eval" / f"step{i}" / "test_behavior.py"
            ev.parent.mkdir(parents=True, exist_ok=True)
            ev.write_text(step["tests"], encoding="utf-8", newline="\n")
            rf = ref_files(t, i)
            write_tree(rf, HERE / tid / "reference" / f"step{i}")

    # manifest（最后写 = 冻结标记）
    task_entries = []
    for t in TASKS:
        proj_fp = {
            rel: _sha(content.encode("utf-8"))
            for rel, content in sorted(t["files"].items())
        }
        proj_agg = _sha("\n".join(f"{k}:{v}" for k, v in sorted(proj_fp.items()))
                        .encode("utf-8"))
        steps_meta = []
        eval_sha = {}
        ref_sha = {}
        for i, s in enumerate(t["steps"], 1):
            ev_h = _sha(s["tests"].encode("utf-8"))
            eval_sha[f"step{i}"] = ev_h
            rf = ref_files(t, i)
            r_agg = _sha("\n".join(
                f"{k}:{_sha(v.encode('utf-8'))}" for k, v in sorted(rf.items())
            ).encode("utf-8"))
            ref_sha[f"step{i}"] = r_agg
            steps_meta.append({
                "id": f"step{i}",
                "instruction_sha256": _sha(s["instruction"].encode("utf-8")),
                "eval_tests_sha256": ev_h,
                "expected_edit_targets": sorted(s.get("expect_targets", [])),
            })
        task_entries.append({
            "id": t["id"], "type": t["type"], "family": t["family"],
            "difficulty": t["difficulty"],
            "project_files_sha256": proj_fp,
            "project_aggregate_sha256": proj_agg,
            "eval_tests_sha256": eval_sha,
            "reference_aggregate_sha256": ref_sha,
            "info_points": t["info_points"],
            "steps": steps_meta,
        })

    info_stats = {
        "total": sum(len(t["info_points"]) for t in TASKS),
        "by_type": {},
        "redundant_in_instruction": sum(
            1 for t in TASKS for ip in t["info_points"]
            if ip["redundant_in_instruction"]
        ),
    }
    for t in TASKS:
        for ip in t["info_points"]:
            info_stats["by_type"][ip["type"]] = (
                info_stats["by_type"].get(ip["type"], 0) + 1
            )

    manifest = {
        "schema": "independent-v1-manifest",
        "frozen_at": frozen_at,
        "prereg_sha256": PREREG_SHA256,
        "design_sha256": DESIGN_SHA256,
        "independent_tasks_sha256": tasks_sha,
        "counts": {
            "tasks": 48, "short": 16, "medium": 16, "long": 16,
            "steps_total": sum(len(t["steps"]) for t in TASKS),
            "archetypes": 24,
        },
        "archetype_counts": {
            f: sum(1 for t in TASKS if t["family"] == f) for f in fams
        },
        "info_points": info_stats,
        "tasks": task_entries,
        "independence": {
            "hash_intersection_with_v1_holdout_p1": [],
            "instruction_overlap_with_v1_holdout_p1": [],
            "forbidden_terms": [],
            "method": "sha256 over prior sets' files (no .json); normalized "
                      "containment for instructions; case-insensitive term scan",
        },
        "validation": {
            "discriminating_checks": len(validation["discriminating"]),
            "targets_checks": len(validation["targets_ok"]),
            "records": validation["records"],
        },
        "freeze_policy": "generated + validated + materialized then frozen; "
                         "manifest written last; no edits after any model request",
        "generated_by": "p1/tasks_independent_v1/make_independent_tasks.py",
    }
    mf_path = HERE / "independent_tasks_manifest.json"
    mf_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    mf_sha = _sha(mf_path.read_bytes())

    total_steps = sum(len(t["steps"]) for t in TASKS)
    print("INDEPENDENT TASK SET FROZEN")
    print(f"  tasks=48 steps_total={total_steps} archetypes=24 "
          f"(short16×2 medium16×5 long16×10)")
    print(f"  info_points={info_stats}")
    print(f"  discriminating={len(validation['discriminating'])} "
          f"targets={len(validation['targets_ok'])}")
    print(f"  independent_tasks.json sha256: {tasks_sha}")
    print(f"  independent_tasks_manifest.json sha256: {mf_sha}")
    print(f"  planned requests = steps×3 arms×R5 = {total_steps * 3 * 5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
