"""independent-v1 任务集共享校验：ops 引擎、参考解、逐题验证（供 make/smoke 复用）。"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
sys.path.insert(0, str(P1 / "scripts"))
from p1_common import run_eval  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402

# 设计文档 §6 禁词（大小写不敏感；中文按子串）
FORBIDDEN = [
    "memory", "上下文", "记忆", "复用", "reuse", "context",
    "REUSE_KV", "symbol_full", "memory_off", "V12",
]


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def apply_ops(files: dict[str, str], ops: list) -> dict[str, str]:
    out = dict(files)
    for op in ops:
        kind = op[0]
        if kind == "replace":
            _, f, old, new = op
            assert f in out, f"replace target missing: {f}"
            n = out[f].count(old)
            assert n == 1, f"replace match count {n} != 1 in {f} for {old[:80]!r}"
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
    files = dict(task["files"])
    for step in task["steps"][:upto]:
        files = apply_ops(files, step["ops"])
    return files


def write_tree(files: dict[str, str], root: Path) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")


def symbol_map(files: dict[str, str]) -> dict[str, list[str]]:
    m: dict[str, list[str]] = {}
    for rel, src in files.items():
        if not rel.endswith(".py"):
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                m.setdefault(node.name, []).append(rel)
    return m


def scan_forbidden(tasks: list) -> list[str]:
    """禁词扫描：指令 + 项目文件（设计文档 §6.1）。"""
    hits: list[str] = []
    for t in tasks:
        for i, s in enumerate(t["steps"], 1):
            low = s["instruction"].lower()
            for term in FORBIDDEN:
                if term.lower() in low:
                    hits.append(f"{t['id']}/step{i}/instruction:{term}")
        for rel, content in t["files"].items():
            low = content.lower()
            for term in FORBIDDEN:
                if term.lower() in low:
                    hits.append(f"{t['id']}/{rel}:{term}")
    return hits


def validate_task(
    t: dict,
    tmp_root: Path,
    prior_hashes: set[str],
    prior_instructions: set[str],
) -> dict:
    """单题验证（设计文档 §7.1–7.3、§6.2–6.3 的题内部分）。返回记录。"""
    tid = t["id"]
    rec = {"id": tid, "discriminating": [], "targets_ok": [],
           "info_ok": False, "hash_ok": True, "overlap": [], "balance_ok": False}
    files_sorted = sorted(t["files"])
    droot = tmp_root / tid
    for i, step in enumerate(t["steps"], 1):
        (droot / "eval" / f"step{i}").mkdir(parents=True, exist_ok=True)
        (droot / "eval" / f"step{i}" / "test_behavior.py").write_text(
            step["tests"], encoding="utf-8", newline="\n"
        )
    for i, step in enumerate(t["steps"], 1):
        ev = droot / "eval" / f"step{i}"
        prev = droot / f"ref{i-1}"
        write_tree(ref_files(t, i - 1), prev)
        ok_prev, out_prev = run_eval(prev, ev, timeout=60)
        assert not ok_prev, (
            f"{tid} step{i}: eval passes on ref_{i-1} (not discriminating)\n{out_prev[-500:]}"
        )
        cur = droot / f"ref{i}"
        write_tree(ref_files(t, i), cur)
        ok_cur, out_cur = run_eval(cur, ev, timeout=60)
        assert ok_cur, (
            f"{tid} step{i}: eval fails on ref_{i}\n{out_cur[-800:]}"
        )
        rec["discriminating"].append(f"step{i}")
        smap_i = symbol_map(ref_files(t, i - 1))
        got = set(parse_edit_targets(step["instruction"], files_sorted, smap_i).exact_paths)
        want = set(step.get("expect_targets", []))
        assert got == want, f"{tid} step{i}: targets {got} != expected {want}"
        rec["targets_ok"].append(f"step{i}")
    # 信息点结构 + 平衡（§5：至少 1 个 redundant true、1 个 false）
    red_true = red_false = 0
    for ip in t["info_points"]:
        for bs in ip["needed_by_steps"]:
            assert 1 <= bs <= len(t["steps"]), f"{tid} info {ip['id']} bad step {bs}"
        assert ip["type"] in ("implementation", "interface", "critical_data", "history")
        assert isinstance(ip["redundant_in_instruction"], bool)
        if ip["redundant_in_instruction"]:
            red_true += 1
        else:
            red_false += 1
    rec["info_ok"] = True
    rec["balance_ok"] = red_true >= 1 and red_false >= 1
    assert rec["balance_ok"], (
        f"{tid}: info point balance violated (true={red_true}, false={red_false})"
    )
    # 跨集文件哈希交集
    for rel, content in t["files"].items():
        if _sha(content.encode("utf-8")) in prior_hashes:
            rec["hash_ok"] = False
            rec["overlap"].append(f"file:{rel}")
    # 跨集指令包含
    for step in t["steps"]:
        mine = step["instruction"].strip()
        for other in prior_instructions:
            if mine == other or mine in other or other in mine:
                rec["overlap"].append(f"instr:{mine[:40]}")
    assert rec["hash_ok"] and not rec["overlap"], f"{tid}: {rec['overlap'][:3]}"
    return rec


def load_prior_sets() -> tuple[set[str], set[str]]:
    """v1 + holdout + P1 的文件哈希全集与指令全集（§6.2）。"""
    prior_hashes: set[str] = set()
    prior_instructions: set[str] = set()
    for base in (P1 / "tasks", P1 / "tasks_v13_holdout", P1 / "tasks_p1_validation"):
        for p in base.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and ".json" not in p.name:
                prior_hashes.add(_sha(p.read_bytes()))
    for rel in ("tasks/tasks_v1.0.json", "tasks_v13_holdout/holdout_tasks.json",
                "tasks_p1_validation/p1_tasks.json"):
        meta = json.loads((P1 / rel).read_text(encoding="utf-8"))
        for e in meta["episodes"]:
            for s in e["steps"]:
                prior_instructions.add(s["instruction"].strip())
    return prior_hashes, prior_instructions


def check_within_set(tasks: list) -> None:
    """集内指令唯一且互不包含（§6.3）。"""
    ins = [s["instruction"].strip() for t in tasks for s in t["steps"]]
    assert len(ins) == len(set(ins)), "duplicate instructions within set"
    for i in range(len(ins)):
        for j in range(i + 1, len(ins)):
            a, b = ins[i], ins[j]
            assert a not in b and b not in a, f"instruction containment: {a[:50]!r} vs {b[:50]!r}"


def validate_all(tasks: list) -> dict:
    prior_hashes, prior_instructions = load_prior_sets()
    forbidden = scan_forbidden(tasks)
    assert not forbidden, f"forbidden terms: {forbidden[:10]}"
    check_within_set(tasks)
    validation = {"discriminating": [], "targets_ok": [], "records": [],
                  "forbidden": [], "hash_intersection": [], "instruction_overlap": []}
    tmp_root = Path(tempfile.mkdtemp(prefix="ind_val_"))
    try:
        for t in tasks:
            rec = validate_task(t, tmp_root, prior_hashes, prior_instructions)
            validation["records"].append(rec)
            validation["discriminating"].extend(f"{rec['id']}/{x}" for x in rec["discriminating"])
            validation["targets_ok"].extend(f"{rec['id']}/{x}" for x in rec["targets_ok"])
            validation["hash_intersection"].extend(
                f"{rec['id']}/{x}" for x in rec["overlap"] if x.startswith("file:")
            )
            validation["instruction_overlap"].extend(
                f"{rec['id']}/{x}" for x in rec["overlap"] if x.startswith("instr:")
            )
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    return validation
