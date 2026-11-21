#!/usr/bin/env python
"""P1 确认性任务集生成器（预注册 v1 §5）：48 题 = Short16 / Medium16 / Long16。

- 参数化任务族构建（族结构在 p1_tasks_manifest.json 披露；prereg §5 族敏感性约定）。
- 步数：Short=2、Medium=5、Long=10（落在预注册 1-3 / 4-8 / 9-15 区间）。
- 参考解 = 按步应用 ops（search-replace/add_file，精确唯一匹配）。
- 冻结前验证：每步 eval 在 ref_{i-1} 必失败、在 ref_i 必通过；
  与 v1、tasks_v13_holdout 文件 hash 交集=0；指令零逐字复用。
- 必要信息点（CMR）随任务预声明。
输出：p1_tasks.json / p1_tasks_manifest.json（存在即拒绝重生成 = 冻结一次）。
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
sys.path.insert(0, str(P1 / "scripts"))
from p1_common import run_eval  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402

REV3_SHA256 = "8ceed45d6554ba952a641fbbebb49b4f3eb0f69858c16ba9d58d7025eb9ee13f"
PREREG_SHA256 = "088898a3aec9d08411864ea03ff79ac7ff3e78411ed34a58de89ecd0881cc7ed"

from p1_registry import TASKS, T  # 共享单例（族模块同样从此注册）


# ---------------------------------------------------------------- ops 引擎
def apply_ops(files: dict[str, str], ops: list) -> dict[str, str]:
    out = dict(files)
    for op in ops:
        kind = op[0]
        if kind == "replace":
            _, f, old, new = op
            assert f in out, f"replace target missing: {f}"
            n = out[f].count(old)
            assert n == 1, f"replace match count {n} != 1 in {f} for {old[:60]!r}"
            out[f] = out[f].replace(old, new)
        elif kind == "add":
            _, f, content = op
            assert f not in out, f"add exists: {f}"
            out[f] = content
        elif kind == "remove":
            _, f = op
            assert f in out, f"remove missing: {f}"
            del out[f]
        else:
            raise ValueError(op)
    return out


def ref_files(task: dict, upto: int) -> dict[str, str]:
    """upto=0 → 初始 project；upto=i → 应用前 i 步 ops。"""
    files = dict(task["files"])
    for step in task["steps"][:upto]:
        files = apply_ops(files, step["ops"])
    return files


def write_tree(files: dict[str, str], root: Path) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def symbol_map(files: dict[str, str]) -> dict[str, list[str]]:
    import ast
    m: dict[str, list[str]] = {}
    for rel, src in files.items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                m.setdefault(node.name, []).append(rel)
    return m


def validate_all() -> dict:
    validation = {
        "initial_fail": [], "ref_pass": [], "step_discriminating": [],
        "targets_ok": [], "hash_intersection": [], "instruction_overlap": [],
    }
    # 指令全集（v1 + holdout1）用于逐字复用检查
    v1ins: set[str] = set()
    meta = json.loads((P1 / "tasks" / "tasks_v1.0.json").read_text(encoding="utf-8"))
    for e in meta["episodes"]:
        for s in e["steps"]:
            v1ins.add(s["instruction"].strip())
    hold = json.loads((HERE.parent / "tasks_v13_holdout" / "holdout_tasks.json").read_text(encoding="utf-8"))
    for e in hold["episodes"]:
        for s in e["steps"]:
            v1ins.add(s["instruction"].strip())

    # 文件 hash 全集（v1 全部文件 + holdout 全部文件）
    prior_hashes: set[str] = set()
    for base in (P1 / "tasks", HERE.parent / "tasks_v13_holdout"):
        for p in base.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and ".json" not in p.name:
                prior_hashes.add(_sha(p.read_bytes()))

    tmp_root = Path(tempfile.mkdtemp(prefix="p1_val_"))
    try:
        for t in TASKS:
            tid = t["id"]
            files_sorted = sorted(t["files"])  # 文件集合不随步变（ops 不删文件）
            # 1) 初态必败
            droot = tmp_root / tid
            for i, step in enumerate(t["steps"], 1):
                (droot / "eval" / f"step{i}").mkdir(parents=True, exist_ok=True)
                (droot / "eval" / f"step{i}" / "test_behavior.py").write_text(
                    step["tests"], encoding="utf-8", newline="\n"
                )
            for i, step in enumerate(t["steps"], 1):
                ev = droot / "eval" / f"step{i}"
                # ref_{i-1} 必失败
                prev = droot / f"ref{i-1}"
                write_tree(ref_files(t, i - 1), prev)
                ok_prev, out_prev = run_eval(prev, ev, timeout=60)
                assert not ok_prev, (
                    f"{tid} step{i}: eval passes on ref_{i-1} (not discriminating)\n{out_prev[-500:]}"
                )
                validation["initial_fail" if i == 1 else "step_discriminating"].append(
                    f"{tid}/step{i}"
                )
                # ref_i 必通过
                cur = droot / f"ref{i}"
                write_tree(ref_files(t, i), cur)
                ok_cur, out_cur = run_eval(cur, ev, timeout=60)
                assert ok_cur, (
                    f"{tid} step{i}: eval fails on ref_{i}\n{out_cur[-800:]}"
                )
                validation["ref_pass"].append(f"{tid}/step{i}")
                # 2) 目标解析（符号表 = ref_{i-1} 状态，与运行时 workspace 一致）
                smap_i = symbol_map(ref_files(t, i - 1))
                got = set(parse_edit_targets(step["instruction"], files_sorted, smap_i).exact_paths)
                want = set(step.get("expect_targets", []))
                if want:
                    assert got == want, (
                        f"{tid} step{i}: targets {got} != expected {want}"
                    )
                    validation["targets_ok"].append(f"{tid}/step{i}")
            # 3) 信息点结构
            for ip in t["info_points"]:
                for bs in ip["needed_by_steps"]:
                    assert 1 <= bs <= len(t["steps"]), f"{tid} info {ip['id']} bad step {bs}"
                assert ip["type"] in ("implementation", "interface", "critical_data", "history")
                assert isinstance(ip["redundant_in_instruction"], bool)
            # 4) hash 交集
            for rel, content in t["files"].items():
                h = _sha(content.encode("utf-8"))
                if h in prior_hashes:
                    validation["hash_intersection"].append(f"{tid}/{rel}")
            # 5) 指令逐字复用
            for step in t["steps"]:
                mine = step["instruction"].strip()
                for other in v1ins:
                    if mine == other or mine in other or other in mine:
                        validation["instruction_overlap"].append(tid)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    assert not validation["hash_intersection"], validation["hash_intersection"][:5]
    assert not validation["instruction_overlap"], validation["instruction_overlap"][:5]
    return validation


def main() -> int:
    # 族注册
    import p1_families_short  # noqa: F401
    import p1_families_medium  # noqa: F401
    import p1_families_long  # noqa: F401

    if (HERE / "p1_tasks_manifest.json").exists():
        print("p1_tasks_manifest.json exists (freeze-once). Refusing.", file=sys.stderr)
        return 2

    ids = [t["id"] for t in TASKS]
    assert len(ids) == 48, f"expected 48 tasks, got {len(ids)}"
    assert len(set(ids)) == 48
    diff = [t["difficulty"] for t in TASKS]
    for d, n in (("short", 16), ("medium", 16), ("long", 16)):
        assert diff.count(d) == n, f"{d}: {diff.count(d)} != {n}"
    steps_by_diff = {"short": 2, "medium": 5, "long": 10}
    for t in TASKS:
        assert len(t["steps"]) == steps_by_diff[t["difficulty"]], (
            f"{t['id']}: {len(t['steps'])} steps != {steps_by_diff[t['difficulty']]}"
        )
    all_instr = [s["instruction"] for t in TASKS for s in t["steps"]]
    assert len(all_instr) == len(set(all_instr)), "duplicate instructions within P1 set"

    validation = validate_all()

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
                {"id": f"step{i}", "instruction": s["instruction"], "eval": f"eval/step{i}"}
                for i, s in enumerate(t["steps"], 1)
            ],
            "required_info_points": t["info_points"],
        })
    tasks_doc = {
        "task_set_version": "p1-validation-v1",
        "frozen_at": frozen_at,
        "prereg": "p1/docs/v12f_validation_preregistration.md",
        "prereg_sha256": PREREG_SHA256,
        "quota": {"short": 16, "medium": 16, "long": 16},
        "steps_per_difficulty": steps_by_diff,
        "architectures": ["vam_coder_v1.2_F", "memory_off", "symbol_full_read"],
        "R": 5,
        "randomization_seed_planned": 20261107,
        "frozen_rules": {
            "max_tokens": 2048,
            "bootstrap_seed": 20261102,
            "temperature": 0.0,
            "seed": 0,
            "history_policy": "keep",
        },
        "episodes": episodes,
    }
    (HERE / "p1_tasks.json").write_text(
        json.dumps(tasks_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tasks_sha = _sha((HERE / "p1_tasks.json").read_bytes())

    task_entries = []
    for t in TASKS:
        proj_fp = {
            rel: _sha(content.encode("utf-8")) for rel, content in sorted(t["files"].items())
        }
        proj_agg = _sha("\n".join(f"{k}:{v}" for k, v in sorted(proj_fp.items())).encode("utf-8"))
        steps_meta = []
        eval_sha = {}
        ref_sha = {}
        for i, s in enumerate(t["steps"], 1):
            ev_h = _sha(s["tests"].encode("utf-8"))
            eval_sha[f"step{i}"] = ev_h
            # reference = ref_files(t, i) 聚合
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
            1 for t in TASKS for ip in t["info_points"] if ip["redundant_in_instruction"]
        ),
    }
    for t in TASKS:
        for ip in t["info_points"]:
            info_stats["by_type"][ip["type"]] = info_stats["by_type"].get(ip["type"], 0) + 1

    manifest = {
        "schema": "p1-validation-manifest-v1",
        "frozen_at": frozen_at,
        "prereg_sha256": PREREG_SHA256,
        "plan_sha256": REV3_SHA256,
        "p1_tasks_sha256": tasks_sha,
        "counts": {
            "tasks": 48, "short": 16, "medium": 16, "long": 16,
            "steps_total": sum(len(t["steps"]) for t in TASKS),
        },
        "families": sorted({t["family"] for t in TASKS}),
        "family_counts": {
            f: sum(1 for t in TASKS if t["family"] == f)
            for f in sorted({t["family"] for t in TASKS})
        },
        "info_points": info_stats,
        "tasks": task_entries,
        "independence": {
            "hash_intersection_with_v1_and_holdout": [],
            "instruction_overlap": [],
            "method": "sha256 over all files; normalized containment for instructions",
        },
        "validation": validation,
        "freeze_policy": "generated + validated then frozen; no edits after any model request",
        "generated_by": "p1/tasks_p1_validation/make_p1_tasks.py",
    }
    (HERE / "p1_tasks_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    mf_sha = _sha((HERE / "p1_tasks_manifest.json").read_bytes())

    total_steps = sum(len(t["steps"]) for t in TASKS)
    print("P1 TASK SET FROZEN")
    print(f"  tasks=48 steps_total={total_steps} "
          f"(short16×2 medium16×5 long16×10)")
    print(f"  info_points={info_stats}")
    print(f"  families={manifest['family_counts']}")
    print(f"  p1_tasks.json sha256: {tasks_sha}")
    print(f"  p1_tasks_manifest.json sha256: {mf_sha}")
    est_req = total_steps * 3 * 5
    print(f"  planned requests = steps×3 archs×R5 = {est_req}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
