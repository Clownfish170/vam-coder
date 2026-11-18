"""V1.3A_CR 单元测试：Normalize/Dedup/Resolve/Compact/装配形态/E-C 不变式。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cr.resolver import (  # noqa: E402
    CrResolveError,
    Reference,
    compact_source,
    mem_block,
    resolve_ref,
    slice_body,
)
from cr.select import select_refs  # noqa: E402
from cr.store import (  # noqa: E402
    CrStoreError,
    MemoryStore,
    content_id_of,
    normalize_body,
    pin_sha256,
)
from cr.validate import validate_cr  # noqa: E402
from v11.visibility import VisibilityTracker, content_sha256  # noqa: E402
from v12.assemble import assemble_v12  # noqa: E402
from v12.config import load_arm  # noqa: E402
from v12.levels import build_plan  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402


def _mk_ws(tmp_path: Path, files: dict[str, str]) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir(parents=True, exist_ok=True)
    for rel, body in files.items():
        p = ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return ws


# ---- store ----
def test_normalize_deterministic():
    a = normalize_body("def f():\r\n    return 1\r\n\r\n")
    b = normalize_body("def f():\n    return 1\n")
    assert a == b
    assert content_id_of(a) == content_id_of(b)
    assert pin_sha256(a) == pin_sha256(b)


def test_dedup_hit_and_collision_guard():
    st = MemoryStore()
    u1, hit1 = st.put_raw("x = 1\n", kind="signature")
    u2, hit2 = st.put_raw("x = 1\n", kind="signature")
    assert hit1 is False and hit2 is True
    assert u1.content_id == u2.content_id
    assert len(st) == 1
    # 同 id 不同 pin 不可能通过 put_raw（内容寻址）；完整性检查
    assert st.integrity_check(u1.content_id)


def test_empty_source_full_rejected():
    st = MemoryStore()
    try:
        st.put_raw("   \n", kind="source_full")
        raise AssertionError("should raise")
    except CrStoreError as e:
        assert e.code == "EMPTY_BODY"


def test_slot_update_and_version_pin():
    st = MemoryStore()
    st.update_slot("S:api", "v1 = 1\n", auto_create=True)
    st.update_slot("S:api", "v2 = 2\n")
    slot = st.get_slot("S:api")
    assert slot is not None and slot.current_version == 2
    ref = Reference(
        path="a.py",
        ref_kind="slot",
        slot_id="S:api",
        version=1,
        pin_sha256=slot.history[1][1],
        range_kind="full",
    )
    body = resolve_ref(ref, st)
    assert "v1" in body
    # 旧版本钉扎仍可解析；version=99 失败
    bad = Reference(path="a.py", ref_kind="slot", slot_id="S:api", version=99, range_kind="full")
    try:
        resolve_ref(bad, st)
        raise AssertionError("should raise")
    except CrResolveError as e:
        assert e.code == "VERSION_NOT_FOUND"


# ---- resolve ----
def test_resolve_not_found_no_silent():
    st = MemoryStore()
    ref = Reference(path="a.py", content_id="C:deadbeef0000", pin_sha256="00", range_kind="full")
    try:
        resolve_ref(ref, st)
        raise AssertionError("should raise")
    except CrResolveError as e:
        assert e.code == "NOT_FOUND"


def test_resolve_hash_mismatch():
    st = MemoryStore()
    u, _ = st.put_raw("body\n", kind="signature")
    ref = Reference(
        path="a.py",
        content_id=u.content_id,
        pin_sha256="f" * 64,
        range_kind="full",
    )
    try:
        resolve_ref(ref, st)
        raise AssertionError("should raise")
    except CrResolveError as e:
        assert e.code == "HASH_MISMATCH"


def test_slice_illegal_range():
    st = MemoryStore()
    u, _ = st.put_raw("a\nb\nc\n", kind="signature")
    ref = Reference(
        path="a.py",
        content_id=u.content_id,
        pin_sha256=u.pin_sha256,
        range_kind="lines",
        line_start=9,
        line_end=10,
    )
    try:
        resolve_ref(ref, st)
        raise AssertionError("should raise")
    except CrResolveError as e:
        assert e.code == "ILLEGAL_RANGE"


def test_compact_keeps_hit_full_and_parses():
    src = "import os\n\ndef alpha(x):\n    return x + 1\n\ndef beta(y):\n    return y * 2\n"
    body, kind = compact_source(src, instruction="修改 alpha")
    assert kind == "signature"
    assert "def alpha" in body and "return x + 1" in body  # 命中完整
    assert "def beta" in body
    assert "return y * 2" not in body  # 未命中 → 合法桩
    import ast as _ast
    _ast.parse(body)  # 桩必须是合法 Python
    assert "..." in body


def test_compact_stub_is_valid_python():
    src = "SIDE = 1\n\n\ndef side_fn():\n    return SIDE\n"
    body, kind = compact_source(src, instruction="修改 gamma")  # 未命中 side_fn
    import ast as _ast
    assert kind == "signature"
    _ast.parse(body)
    assert "def side_fn" in body and "..." in body


def test_compact_syntax_error_falls_back_full():
    src = "def broken(:\n"
    body, kind = compact_source(src, "")
    assert kind == "source_full"
    assert body == src


def test_mem_block_always_has_body():
    b = mem_block("C:abc", "signature", "def f(): ...\n", path="a.py")
    assert b.startswith("--- MEM id=C:abc")
    assert "def f()" in b
    assert "C:abc" in b.split("\n")[0]
    # 正文行非空
    lines = b.strip().split("\n")
    assert len(lines) >= 2 and lines[1].strip()


# ---- assemble CR form gate ----
def test_cr_related_mem_and_et_still_file(tmp_path):
    files = {
        "hot.py": "def hot():\n    return 1\n",
        "stable.py": "def stable_helper(a):\n    return a\n\ndef other(b):\n    return b\n",
    }
    ws = _mk_ws(tmp_path, files)
    instruction = "修改 hot.py 返回 2"
    flist = sorted(files)
    targets = parse_edit_targets(instruction, flist, {})
    cfg = load_arm("V13ACR")
    assert cfg.cr_enabled and cfg.cr_related_mode == "compact"
    sha = {f: content_sha256(files[f]) for f in flist}
    sizes = {f: len(files[f]) for f in flist}
    entries = {
        f: [{"symbol_id": f"e:{f}::x", "validity": "valid", "deps": []}]
        for f in flist
    }
    plan = build_plan(
        arm_cfg=cfg,
        instruction=instruction,
        workspace_files=flist,
        workspace_sha=sha,
        file_sizes=sizes,
        entries_by_file=entries,
        targets=targets,
        system_history_tokens_est=0,
        source_by_file=files,
    )
    store = MemoryStore()
    ctx = assemble_v12(
        ws,
        plan,
        VisibilityTracker(),
        cfg,
        cr_store=store,
        cr_instruction=instruction,
    )
    # ET 必须 FILE
    assert "--- FILE hot.py (full current source) ---" in ctx.text
    # 相关非目标：1.5B 实证后改为跳过注入（禁止 MEM/紧凑正文进 Prompt）
    related = {
        f.relpath
        for f in plan.files
        if f.level == "FULL" and not f.is_must and not f.is_edit_target and not f.is_candidate
    }
    if "stable.py" in related:
        assert any(
            a["file"] == "stable.py" and a["action"] == "CR_RELATED_SKIPPED"
            for a in ctx.audits
        )
        assert "--- MEM id=" not in ctx.text
        assert "--- FILE stable.py" not in ctx.text
    assert ctx.insufficient is False


def test_cr_disabled_matches_v12f_no_mem(tmp_path):
    files = {
        "hot.py": "def hot():\n    return 1\n",
        "stable.py": "def stable_helper(a):\n    return a\n",
    }
    ws = _mk_ws(tmp_path, files)
    instruction = "修改 hot.py 返回 2"
    flist = sorted(files)
    targets = parse_edit_targets(instruction, flist, {})
    cfg = load_arm("F")  # cr off
    assert cfg.cr_enabled is False
    sha = {f: content_sha256(files[f]) for f in flist}
    sizes = {f: len(files[f]) for f in flist}
    entries = {
        f: [{"symbol_id": f"e:{f}::x", "validity": "valid", "deps": []}]
        for f in flist
    }
    plan = build_plan(
        arm_cfg=cfg,
        instruction=instruction,
        workspace_files=flist,
        workspace_sha=sha,
        file_sizes=sizes,
        entries_by_file=entries,
        targets=targets,
        system_history_tokens_est=0,
        source_by_file=files,
    )
    ctx = assemble_v12(ws, plan, VisibilityTracker(), cfg, cr_store=MemoryStore())
    assert "--- MEM " not in ctx.text
    assert ctx.mem_blocks == 0


def test_validate_cr_required_missing(tmp_path):
    st = MemoryStore()
    u, _ = st.put_raw("x=1\n", kind="signature")
    ref = Reference(path="rel.py", content_id=u.content_id, pin_sha256=u.pin_sha256, range_kind="full")
    # required 含 et.py，delivered 为空 → DEP_INCOMPLETE
    check = validate_cr(
        [ref],
        st,
        required_paths={"et.py"},
        delivered_paths=set(),
    )
    assert not check.ok
    assert any(c.startswith("DEP_INCOMPLETE") for c in check.codes)


def test_select_forces_must_and_related(tmp_path):
    files = {"hot.py": "def hot():\n    return 1\n", "s.py": "def s():\n    return 0\n"}
    instruction = "修改 hot.py"
    flist = sorted(files)
    targets = parse_edit_targets(instruction, flist, {})
    cfg = load_arm("V13ACR")
    sha = {f: content_sha256(files[f]) for f in flist}
    sizes = {f: len(files[f]) for f in flist}
    entries = {
        f: [{"symbol_id": f"e:{f}::x", "validity": "valid", "deps": []}]
        for f in flist
    }
    plan = build_plan(
        arm_cfg=cfg,
        instruction=instruction,
        workspace_files=flist,
        workspace_sha=sha,
        file_sizes=sizes,
        entries_by_file=entries,
        targets=targets,
        system_history_tokens_est=0,
        source_by_file=files,
    )
    st = MemoryStore()
    refs = select_refs(plan, cfg, disk_files=files, store=st)
    paths = {r.path for r in refs}
    assert "hot.py" in paths
    purposes = {r.path: r.purpose for r in refs}
    assert purposes.get("hot.py") == "must"
