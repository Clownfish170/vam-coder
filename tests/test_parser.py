"""解析器测试：符号提取、依赖消解、语言限制记录。"""

from __future__ import annotations

from pathlib import Path

from vam_coder.parser import parse_repo

from conftest import sid


def test_extracts_functions_classes_methods(repo_v1: Path, config):
    result = parse_repo(repo_v1, "demo", config)
    ids = {d.symbol_id for d in result.symbols}
    assert sid("demo", "core.py", "compute") in ids
    assert sid("demo", "core.py", "helper") in ids
    assert sid("demo", "app.py", "run") in ids
    assert sid("demo", "app.py", "lone") in ids
    by_id = {d.symbol_id: d for d in result.symbols}
    assert by_id[sid("demo", "core.py", "compute")].kind == "function"
    # 哈希是确定性的：同一文件两次解析得到相同哈希
    again = parse_repo(repo_v1, "demo", config)
    again_map = {d.symbol_id: d.content_hash for d in again.symbols}
    assert all(again_map[k] == v for k, v in {
        d.symbol_id: d.content_hash for d in result.symbols
    }.items())


def test_resolves_cross_file_dependencies(repo_v1: Path, config):
    result = parse_repo(repo_v1, "demo", config)
    by_id = {d.symbol_id: d for d in result.symbols}
    # helper → compute（同文件）
    helper = by_id[sid("demo", "core.py", "helper")]
    assert sid("demo", "core.py", "compute") in helper.deps
    # run → helper（跨文件）
    run = by_id[sid("demo", "app.py", "run")]
    assert sid("demo", "core.py", "helper") in run.deps
    # lone 无依赖
    lone = by_id[sid("demo", "app.py", "lone")]
    assert lone.deps == []


def test_unsupported_language_recorded(tmp_path: Path, config):
    root = tmp_path / "mixed"
    root.mkdir()
    (root / "main.js").write_text("function f() { return 1; }\n", encoding="utf-8")
    (root / "Main.java").write_text("class Main {}\n", encoding="utf-8")
    (root / "ok.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    result = parse_repo(root, "demo", config)
    reasons = {s["path"]: s["reason"] for s in result.skipped_files}
    assert reasons.get("main.js") == "unsupported_language"
    assert reasons.get("Main.java") == "unsupported_language"
    # 受支持语言照常解析
    assert {d.qualified_name for d in result.symbols} == {"f"}
