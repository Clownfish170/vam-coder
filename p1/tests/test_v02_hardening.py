"""P1-v0.2 加固回归测试（不依赖模型服务）。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = P1_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(P1_ROOT.parent / "src"))

from vam_coder.models import MemoryEntry  # noqa: E402

from p1_common import (  # noqa: E402
    ChatResult,
    assemble_refreshed_summary,
    assemble_vam_coder,
    tokens_estimate_chars,
    trim_history,
)
from run_p1 import (  # noqa: E402
    BASELINES,
    MAIN_BASELINES,
    check_manifest,
    rotation_order,
)


def entry(sid: str, rel: str, source_hash: str = "h1") -> MemoryEntry:
    return MemoryEntry(
        symbol_id=sid, repo_id="ep", file_path=rel,
        qualified_name=sid.split("::")[-1], kind="function",
        content_hash=source_hash, source_hash=source_hash, version=1,
        deps=[], summary="s", validity="valid", kv_ptr="sim://x",
        provenance=None, size_bytes=40, start_line=1, end_line=3,
        last_seen_repo_version=1, updated_at="2026-10-18T00:00:00+00:00",
    )


def test_rotation_reproducible_and_covers_all_positions():
    bases = list(MAIN_BASELINES)
    seen_first = set()
    for rep in range(4):
        order, off = rotation_order(bases, 0, rep)
        assert off == rep % 4
        assert sorted(order) == sorted(bases)
        seen_first.add(order[0])
    assert seen_first == set(bases)  # 4 个 rep 覆盖每个基线都当过队首
    # 同参可复现
    assert rotation_order(bases, 2, 3) == rotation_order(bases, 2, 3)


def test_trim_history_drops_oldest_pairs_keeps_system():
    history = [{"role": "system", "content": "SYS"}]
    for i in range(5):
        history.append({"role": "user", "content": f"U{i} " + "x" * 100})
        history.append({"role": "assistant", "content": f"A{i} " + "y" * 100})
    trimmed, dropped, chars = trim_history(history, max_history_chars=400)
    assert trimmed[0]["role"] == "system"
    assert dropped >= 1
    assert chars <= 400
    # 最新的 user/assistant 对保留
    assert trimmed[-1]["role"] == "assistant"
    assert trimmed[-1]["content"].startswith("A4")
    # 四基线同一函数：结果确定
    t2, d2, c2 = trim_history(history, max_history_chars=400)
    assert t2 == trimmed and d2 == dropped and c2 == chars


def test_trim_history_noop_when_under_budget():
    history = [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "u"},
    ]
    trimmed, dropped, _ = trim_history(history, 10_000)
    assert dropped == 0 and trimmed == history


def test_reuse_metrics_three_levels(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (ws / "b.py").write_text("def g():\n    return 2\n", encoding="utf-8")
    ef = entry("ep:a.py::f", "a.py", "h1")
    eg = entry("ep:b.py::g", "b.py", "h1")
    # a.py：REUSE 命中且无 EXPAND → 文件级省略
    # b.py：REUSE 命中但同文件另有 EXPAND?  单符号 EXPAND 场景另一例
    decisions = [
        {"symbol_id": "ep:a.py::f", "action": "REUSE_KV", "validity": "valid",
         "est_tokens": 1, "reasons": []},
        {"symbol_id": "ep:b.py::g", "action": "EXPAND", "validity": "stale",
         "est_tokens": 1, "reasons": []},
    ]
    ctx = assemble_vam_coder(
        ws, decisions, {"ep:a.py::f": ef, "ep:b.py::g": eg},
        {"ep:a.py::f": "h1", "ep:b.py::g": "h1"},
    )
    assert ctx.reuse_decisions == 1          # 决策级
    assert ctx.reuse_omitted == 1            # 符号级实际省略
    assert ctx.reuse_omitted_files == 1      # 文件级
    assert ctx.reuse_omitted_bytes == len("def f():\n    return 1\n")
    assert ctx.expand_included_bytes == len("def g():\n    return 2\n")
    assert ctx.reuse_without_omission == 0


def test_reuse_decision_without_omission_when_sibling_expands(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "m.py").write_text(
        "def f():\n    return 1\n\ndef g():\n    return 2\n", encoding="utf-8"
    )
    ef = entry("ep:m.py::f", "m.py", "h1")
    eg = entry("ep:m.py::g", "m.py", "h2")
    decisions = [
        {"symbol_id": "ep:m.py::f", "action": "REUSE_KV", "validity": "valid",
         "est_tokens": 1, "reasons": []},
        {"symbol_id": "ep:m.py::g", "action": "EXPAND", "validity": "stale",
         "est_tokens": 1, "reasons": []},
    ]
    ctx = assemble_vam_coder(
        ws, decisions, {"ep:m.py::f": ef, "ep:m.py::g": eg},
        {"ep:m.py::f": "h1"},
    )
    # f 的 REUSE_KV 决策发生了，但同文件因 g 被展开 → 不产生文件级省略
    assert ctx.reuse_decisions == 1
    assert ctx.reuse_omitted == 0
    assert ctx.reuse_omitted_files == 0
    assert ctx.reuse_without_omission == 1
    assert ctx.file_blocks == 1


def test_refreshed_summary_control_has_no_source():
    ctx = assemble_refreshed_summary(
        {
            "ep:a.py::f": {
                "qualified_name": "f", "summary": "f: fresh",
                "validity": "stale", "file_path": "a.py",
            }
        }
    )
    assert "FILE " not in ctx.text
    assert "refreshed" in ctx.text
    assert ctx.summary_blocks == 1


def test_chat_result_has_audit_fields():
    cr = ChatResult(
        text="", prompt_tokens=0, completion_tokens=0, latency_ms=1.0,
        usage_source="none",
    )
    assert cr.http_status is None
    assert cr.response_model is None
    assert cr.started_at is None and cr.ended_at is None


def test_tokens_estimate_is_estimate():
    assert tokens_estimate_chars("abcdefgh") == 2


def test_baseline_sets():
    assert set(MAIN_BASELINES) <= set(BASELINES)
    assert "refreshed_summary" in BASELINES


def test_check_manifest_detects_mismatch(tmp_path):
    live = {
        "tasks_sha256": "aaa",
        "script_sha256": {"run_p1.py": "bbb", "p1_common.py": "ccc"},
        "eval_dir_sha256": {"ep/step1": "ddd"},
        "project_dir_sha256": {"ep": "eee"},
    }
    good = {
        "tasks_sha256": "aaa",
        "script_sha256": {"run_p1.py": "bbb", "p1_common.py": "ccc"},
        "eval_dir_sha256": {"ep/step1": "ddd"},
        "project_dir_sha256": {"ep": "eee"},
    }
    p = tmp_path / "m.json"
    p.write_text(json.dumps(good), encoding="utf-8")
    assert check_manifest(p, live) == []
    bad = dict(good)
    bad["tasks_sha256"] = "zzz"
    p.write_text(json.dumps(bad), encoding="utf-8")
    ms = check_manifest(p, live)
    assert any("tasks_sha256" in m for m in ms)


def test_run_refuses_nonempty_out_dir(tmp_path):
    out = tmp_path / "run"
    out.mkdir()
    (out / "existing.txt").write_text("keep", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "run_p1.py"),
            "--episode", "stale_summary_trap",
            "--baselines", "memory_off",
            "--dry-run", "--out", str(out),
            # v1.0 脚本改动会使 v0.2 清单不匹配（exit 3）；本测试只验证防覆盖守卫
            "--allow-manifest-mismatch",
        ],
        capture_output=True, text=True, timeout=120,
        cwd=str(P1_ROOT.parent),
        encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 2, proc.stderr
    assert "refusing" in (proc.stderr + proc.stdout).lower()
    assert (out / "existing.txt").read_text(encoding="utf-8") == "keep"


def test_trap_step1_eval_rejects_docstring_rewrite(tmp_path):
    import shutil
    import os
    from p1_common import run_eval

    proj = P1_ROOT / "tasks" / "stale_summary_trap" / "project"
    ev = P1_ROOT / "tasks" / "stale_summary_trap" / "eval" / "step1"
    ws = tmp_path / "ws"
    shutil.copytree(proj, ws)
    # 初始状态应失败（UNIT 仍是 10）
    ok, _ = run_eval(ws, ev)
    assert ok is False
    # 仅改常量 → 通过
    p = ws / "pricing.py"
    p.write_text(
        p.read_text(encoding="utf-8").replace("UNIT = 10", "UNIT = 12"),
        encoding="utf-8",
    )
    ok2, _ = run_eval(ws, ev)
    assert ok2 is True
    # 顺手改 docstring → 失败（v0.2 判据）
    p.write_text(
        p.read_text(encoding="utf-8").replace("(=10)", "(=12)"),
        encoding="utf-8",
    )
    ok3, out3 = run_eval(ws, ev)
    assert ok3 is False
    assert "docstring" in out3.lower() or "frozen" in out3.lower()
