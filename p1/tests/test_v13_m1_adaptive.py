"""V1.3-M1 adaptive_a tests + V1.2 E/F/G/H regression."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from p1_common import SYSTEM_PROMPT  # noqa: E402
from v11.visibility import content_sha256  # noqa: E402
from v12.adaptive_features import (  # noqa: E402
    decide_related_level,
    has_implementation_body,
    instruction_hit,
)
from v12.assemble import assemble_v12  # noqa: E402
from v12.config import load_arm  # noqa: E402
from v12.levels import ExpandPlan, FileLevel, build_plan  # noqa: E402
from v12.messages_visibility import verify_omissions_in_messages  # noqa: E402
from v12.proof import tracker_from_history  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402

IMPL = "def clamp(x, lo, hi):\n    return max(lo, min(hi, x))\n"
NO_IMPL = "CONST = 1\n"
SYNTAX_BAD = "def broken(:\n  pass\n"


# --- feature unit tests ---
def test_no_body_digest():
    body, _ = has_implementation_body(NO_IMPL)
    assert body is False
    feat = decide_related_level(
        relpath="cfg.py",
        source=NO_IMPL,
        instruction="修改 cfg.py 的 CONST",
        symbols=None,
        edit_targets={"main.py"},
        file_deps={},
    )
    assert not feat.upgrade_to_full
    assert "no_implementation_body" in feat.reason or "digest" in feat.reason


def test_impl_no_hit_no_dep_digest():
    feat = decide_related_level(
        relpath="util.py",
        source=IMPL,
        instruction="修改 other.py 返回 1",
        symbols=None,
        edit_targets={"other.py"},
        file_deps={"other.py": set()},
    )
    assert feat.implementation_body is True
    assert not feat.instruction_hit
    assert not feat.dependency_touch
    assert not feat.upgrade_to_full


def test_impl_and_instruction_full():
    feat = decide_related_level(
        relpath="util.py",
        source=IMPL,
        instruction="请修改 util.py 中 clamp 的实现",
        symbols=["clamp"],
        edit_targets={"app.py"},
        file_deps={},
    )
    assert feat.upgrade_to_full
    assert feat.instruction_hit


def test_impl_and_dependency_full():
    feat = decide_related_level(
        relpath="util.py",
        source=IMPL,
        instruction="在 app.py 新增 batch",
        symbols=None,
        edit_targets={"app.py"},
        file_deps={"app.py": {"util.py"}},
    )
    assert feat.dependency_touch
    assert feat.upgrade_to_full


def test_impl_both_conditions_full():
    feat = decide_related_level(
        relpath="util.py",
        source=IMPL,
        instruction="修改 util.py 并在 app.py 使用",
        symbols=["clamp"],
        edit_targets={"app.py"},
        file_deps={"app.py": {"util.py"}},
    )
    assert feat.instruction_hit and feat.dependency_touch
    assert feat.upgrade_to_full


def test_uncomputable_conservative_digest():
    feat = decide_related_level(
        relpath="broken.py",
        source=SYNTAX_BAD,
        instruction="修改 broken.py",
        symbols=None,
        edit_targets={"broken.py"},
        file_deps={},
    )
    # if broken.py is also edit target, adaptive only for non-must related;
    # here decide_related_level still conservative on body
    assert feat.upgrade_to_full is False
    assert feat.uncomputable_reason.startswith("syntax_error") or feat.implementation_body is None


def test_instruction_hit_word_boundary():
    ok, _ = instruction_hit("util.py", "修改 util.py 返回", None)
    assert ok
    # stem util without .py should not match path_token but may match stem
    ok2, why = instruction_hit("util.py", "修改 util 返回", None)
    assert ok2 and why == "stem_token"


# --- plan integration: V13A ---
def test_v13a_plan_upgrade_and_audit():
    sources = {
        "util.py": IMPL,
        "app.py": "def batch():\n    return 1\n",
    }
    sha = {k: content_sha256(v) for k, v in sources.items()}
    sizes = {k: len(v.encode()) for k, v in sources.items()}
    entries = {
        "util.py": [{"symbol_id": "u:clamp", "validity": "valid", "deps": []}],
        "app.py": [{"symbol_id": "a:batch", "validity": "valid", "deps": ["u:clamp"]}],
    }
    # only app is edit target; util related non-must if not in must
    # dep of app includes util → util enters must via closure; use instruction-only related
    # Force util as related non-must: no dep from entries of app to util for closure
    entries = {
        "util.py": [{"symbol_id": "u:clamp", "validity": "valid", "deps": []}],
        "app.py": [{"symbol_id": "a:batch", "validity": "valid", "deps": []}],
    }
    targets = parse_edit_targets("在 app.py 新增 batch", ["util.py", "app.py"], {})
    cfg = load_arm("V13A")
    assert cfg.non_target_related == "adaptive_a"
    plan = build_plan(
        arm_cfg=cfg,
        instruction="在 app.py 新增 batch 并使用 util.py",
        workspace_files=["util.py", "app.py"],
        workspace_sha=sha,
        file_sizes=sizes,
        entries_by_file=entries,
        targets=targets,
        source_by_file=sources,
    )
    assert "app.py" in plan.edit_targets
    by = {f.relpath: f for f in plan.files}
    assert by["app.py"].level == "FULL" and by["app.py"].is_edit_target
    # util: impl + instruction hit → FULL related
    assert by["util.py"].level == "FULL"
    assert any(a["relpath"] == "util.py" for a in plan.adaptive_audit)


def test_v13a_default_digest_when_no_signal():
    sources = {"cfg.py": NO_IMPL, "main.py": "x = 1\n"}
    sha = {k: content_sha256(v) for k, v in sources.items()}
    sizes = {k: len(v.encode()) for k, v in sources.items()}
    entries = {
        "cfg.py": [{"symbol_id": "c", "validity": "valid", "deps": []}],
        "main.py": [{"symbol_id": "m", "validity": "valid", "deps": []}],
    }
    # related via stem "cfg" in instruction, but not edit target (no cfg.py token)
    targets = parse_edit_targets("修改 main.py；参考 cfg 配置", ["cfg.py", "main.py"], {})
    plan = build_plan(
        arm_cfg=load_arm("V13A"),
        instruction="修改 main.py；参考 cfg 配置",
        workspace_files=["cfg.py", "main.py"],
        workspace_sha=sha,
        file_sizes=sizes,
        entries_by_file=entries,
        targets=targets,
        source_by_file=sources,
    )
    by = {f.relpath: f for f in plan.files}
    assert by["main.py"].is_edit_target and by["main.py"].level == "FULL"
    # cfg related (stem) but no impl body → DIGEST
    assert by["cfg.py"].level == "DIGEST", by["cfg.py"]
    audit = {a["relpath"]: a for a in plan.adaptive_audit}
    assert audit["cfg.py"]["implementation_body"] is False


def test_efgh_unchanged_configs():
    e, f, g, h = load_arm("E"), load_arm("F"), load_arm("G"), load_arm("H")
    assert e.non_target_related == "digest"
    assert f.non_target_related == "full"
    assert g.non_target_related == "full_if_indexed"
    assert h.non_target_related == "none"
    for a in (e, f, g, h):
        assert a.edit_target_oprime_forbid
        assert a.candidate_full_oprime_forbid


def test_et_must_always_full_with_v13a(tmp_path):
    (tmp_path / "hot.py").write_text(IMPL, encoding="utf-8")
    plan = ExpandPlan(
        arm="V13A",
        edit_targets={"hot.py"},
        files=[
            FileLevel(
                relpath="hot.py",
                level="FULL",
                is_must=True,
                is_edit_target=True,
            )
        ],
    )
    ctx = assemble_v12(tmp_path, plan, tracker_from_history([{"role": "system", "content": SYSTEM_PROMPT}]), load_arm("V13A"), record_context_marks=False)
    assert "--- FILE hot.py" in ctx.text
    assert "hot.py" not in ctx.omitted_files


def test_vp_fail_insufficient_no_model():
    # reuse verify path: missing ET in current context
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "--- INDEX hot.py ---\n\n=== OUTPUT ===\nx"},
    ]
    check = verify_omissions_in_messages(
        msgs, [], {"hot.py": content_sha256(IMPL)}, edit_targets=["hot.py"], candidate_full=[]
    )
    assert not check.edit_target_full_verified
    assert not check.ok
