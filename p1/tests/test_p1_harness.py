"""P1 脚手架回归测试（不依赖模型服务；对应审计修复记录）。"""

from __future__ import annotations

import sys
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P1_ROOT / "scripts"))
sys.path.insert(0, str(P1_ROOT.parent / "src"))

from vam_coder.models import MemoryEntry  # noqa: E402

from p1_common import (  # noqa: E402
    apply_blocks,
    assemble_fixed_summary,
    assemble_memory_off,
    assemble_vam_coder,
    parse_file_blocks,
    posix,
)


def entry(
    sid: str,
    rel: str,
    source_hash: str = "h1",
    validity: str = "valid",
    summary: str | None = "sum",
) -> MemoryEntry:
    return MemoryEntry(
        symbol_id=sid,
        repo_id="ep",
        file_path=rel,
        qualified_name=sid.split("::")[-1],
        kind="function",
        content_hash=source_hash,
        source_hash=source_hash,
        version=1,
        deps=[],
        summary=summary,
        validity=validity,
        kv_ptr="sim://kv/x",
        provenance=None,
        size_bytes=40,
        start_line=1,
        end_line=3,
        last_seen_repo_version=1,
        updated_at="2026-10-18T00:00:00+00:00",
    )


def test_posix_normalizes_backslash():
    assert posix("a\\b.py") == "a/b.py"


def test_parse_file_blocks_roundtrip():
    text = (
        "noise\n"
        "FILE: pkg/mod.py\n"
        "```python\n"
        "x = 1\n"
        "```\n"
        "tail"
    )
    blocks = parse_file_blocks(text)
    assert blocks == [("pkg/mod.py", "x = 1\n")]


def test_apply_blocks_rejects_path_escape_and_eval(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    applied, rejected = apply_blocks(
        ws,
        [
            ("../evil.py", "x=1\n"),
            ("eval/test_x.py", "x=1\n"),
            ("/abs/evil.py", "x=1\n"),
            ("ok.py", "x = 1\n"),
        ],
    )
    assert applied == ["ok.py"]
    assert len(rejected) == 3
    assert (ws / "ok.py").read_text(encoding="utf-8") == "x = 1\n"
    assert not (tmp_path / "evil.py").exists()


def test_windows_style_file_block_applies(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    applied, rejected = apply_blocks(ws, [("sub\\mod.py", "y=2\n")])
    assert applied == ["sub/mod.py"]
    assert (ws / "sub" / "mod.py").is_file()
    assert rejected == []


def _decisions(*pairs):
    return [
        {"symbol_id": sid, "action": act, "validity": "valid",
         "est_tokens": 1, "reasons": []}
        for sid, act in pairs
    ]


def test_vam_reuse_omitted_only_when_hash_matches(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    e = entry("ep:a.py::f", "a.py", source_hash="h1")
    # 历史中已有相同哈希 → 省略
    ctx = assemble_vam_coder(
        ws, _decisions(("ep:a.py::f", "REUSE_KV")), {"ep:a.py::f": e},
        {"ep:a.py::f": "h1"},
    )
    assert ctx.reuse_omitted == 1
    assert "FILE a.py" not in ctx.text
    # 历史缺失 → 回退读取当前源码（不能假装复用）
    ctx2 = assemble_vam_coder(
        ws, _decisions(("ep:a.py::f", "REUSE_KV")), {"ep:a.py::f": e}, {}
    )
    assert ctx2.reuse_omitted == 0
    assert "--- FILE a.py" in ctx2.text
    assert "return 1" in ctx2.text


def test_vam_same_file_expand_dedup(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "m.py").write_text("def f():\n    return 1\n\ndef g():\n    return 2\n",
                             encoding="utf-8")
    ef = entry("ep:m.py::f", "m.py")
    eg = entry("ep:m.py::g", "m.py", source_hash="h2", validity="stale")
    ctx = assemble_vam_coder(
        ws,
        _decisions(("ep:m.py::f", "REUSE_KV"), ("ep:m.py::g", "EXPAND")),
        {"ep:m.py::f": ef, "ep:m.py::g": eg},
        {"ep:m.py::f": "h1"},  # f 哈希不匹配 → 本可回退；g EXPAND → 整文件一次
    )
    assert ctx.file_blocks == 1
    assert ctx.text.count("--- FILE m.py") == 1


def test_fixed_summary_has_no_source_blocks():
    frozen = {
        "ep:a.py::f": {
            "qualified_name": "f", "summary": "f: note",
            "validity": "valid", "file_path": "a.py",
        }
    }
    ctx = assemble_fixed_summary(frozen)
    assert "FILE " not in ctx.text
    assert "MEMORY SUMMARY" in ctx.text
    assert ctx.summary_blocks == 1


def test_memory_off_includes_all_py_files(tmp_path):
    ws = tmp_path / "ws"
    (ws / "sub").mkdir(parents=True)
    (ws / "a.py").write_text("A=1\n", encoding="utf-8")
    (ws / "sub" / "b.py").write_text("B=2\n", encoding="utf-8")
    (ws / "note.txt").write_text("ignore\n", encoding="utf-8")
    ctx = assemble_memory_off(ws)
    assert ctx.file_blocks == 2
    assert "--- FILE a.py" in ctx.text
    assert "--- FILE sub/b.py" in ctx.text
    assert "note.txt" not in ctx.text
