"""V1.1 EMC 与装配回退单测。"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v11.assemble import assemble_vam_v11  # noqa: E402
from v11.controller import FilePlan, MemoryController  # noqa: E402
from v11.visibility import VisibilityTracker, content_sha256  # noqa: E402


def test_emc_no_need_without_hint():
    c = MemoryController()
    plan = c.decide(
        instruction="你好世界",
        workspace_files=["a.py"],
        entries_by_file={"a.py": [{"symbol_id": "r:a.py::f", "validity": "valid"}]},
        visibility_paths=set(),
        dependency_closure_files=set(),
    )
    assert plan.need is False
    assert "R2_no_need" in plan.rules_fired


def test_emc_edit_hint_selects_files():
    c = MemoryController()
    plan = c.decide(
        instruction="修改 hot.py 返回 2",
        workspace_files=["hot.py", "stable_a.py"],
        entries_by_file={
            "hot.py": [{"symbol_id": "r:hot.py::hot", "validity": "valid"}],
            "stable_a.py": [{"symbol_id": "r:stable_a.py::fa", "validity": "valid"}],
        },
        visibility_paths=set(),
        dependency_closure_files=set(),
    )
    assert plan.need is True
    paths = {f.relpath for f in plan.files}
    assert "hot.py" in paths


def test_assemble_visibility_veto_fallback_expand():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        (ws / "hot.py").write_text("def hot():\n    return 1\n", encoding="utf-8")
        (ws / "stable_a.py").write_text('def fa():\n    return "A"\n', encoding="utf-8")
        tr = VisibilityTracker()
        # 历史 assistant 只有 hot，没有 stable —— 二者都无 context 可见证明
        sha_hot = content_sha256("def hot():\n    return 1\n")
        sha_sa = content_sha256('def fa():\n    return "A"\n')
        plans = [
            FilePlan(relpath="hot.py", action="REUSE_KV", content_sha256=sha_hot),
            FilePlan(relpath="stable_a.py", action="REUSE_KV", content_sha256=sha_sa),
        ]
        ctx = assemble_vam_v11(ws, plans, tr, mode_banner="short")
        # O′ 全部失败 → 全部回退 EXPAND
        assert ctx.fallback_events == 2
        assert ctx.file_blocks == 2
        assert ctx.verified_safe_omissions == 0
        assert "hot.py" in ctx.text and "stable_a.py" in ctx.text


def test_assemble_omits_when_visible():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        body = "def hot():\n    return 1\n"
        (ws / "hot.py").write_text(body, encoding="utf-8")
        tr = VisibilityTracker()
        ctx0 = f"--- FILE hot.py (full current source) ---\n{body.rstrip()}\n"
        tr.mark_from_context(ctx0)
        plans = [
            FilePlan(
                relpath="hot.py",
                action="REUSE_KV",
                content_sha256=content_sha256(body),
            )
        ]
        ctx = assemble_vam_v11(ws, plans, tr, mode_banner="none")
        assert ctx.verified_safe_omissions == 1
        assert ctx.file_blocks == 0
        assert "hot.py" not in ctx.text.split("FILE")[-1] if "FILE" in ctx.text else True


def test_assemble_does_not_fabricate_missing_file():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        tr = VisibilityTracker()
        plans = [FilePlan(relpath="ghost.py", action="EXPAND")]
        ctx = assemble_vam_v11(ws, plans, tr)
        assert ctx.insufficient is True
        assert "ghost.py" not in ctx.text


def test_visibility_veto_on_plan():
    c = MemoryController()
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        (ws / "hot.py").write_text("def hot():\n    return 1\n", encoding="utf-8")
        plan = c.decide(
            instruction="hot() 返回 2",
            workspace_files=["hot.py"],
            entries_by_file={
                "hot.py": [
                    {
                        "symbol_id": "r:hot.py::hot",
                        "validity": "valid",
                        "source_hash": content_sha256("def hot():\n    return 1\n"),
                    }
                ]
            },
            visibility_paths=set(),
            dependency_closure_files={"hot.py"},
        )
        tr = VisibilityTracker()
        sha_map = {"hot.py": content_sha256("def hot():\n    return 1\n")}
        plan2 = c.apply_visibility_veto(plan, tr, sha_map)
        assert all(f.action == "EXPAND" for f in plan2.files)
