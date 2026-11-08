"""P1-v1.0 审计/脱敏/机制检查器回归测试（不依赖模型服务）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = P1_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(P1_ROOT.parent / "src"))

from vam_coder.models import MemoryEntry  # noqa: E402

from check_mechanisms_v1 import (  # noqa: E402
    check_run,
    match_event,
    sha256_file,
    slice_invalidation_by_step,
)
from p1_common import (  # noqa: E402
    assemble_vam_coder,
    history_code_metrics,
    redact_assistant_code,
)
from run_p1 import CSV_FIELDS  # noqa: E402


def entry(sid: str, rel: str, source_hash: str = "h1") -> MemoryEntry:
    return MemoryEntry(
        symbol_id=sid, repo_id="ep", file_path=rel,
        qualified_name=sid.split("::")[-1], kind="function",
        content_hash=source_hash, source_hash=source_hash, version=1,
        deps=[], summary="s", validity="valid", kv_ptr="sim://x",
        provenance=None, size_bytes=40, start_line=1, end_line=3,
        last_seen_repo_version=1, updated_at="2026-10-18T00:00:00+00:00",
    )


def _dec(sid, act):
    return {"symbol_id": sid, "action": act, "validity": "valid",
            "est_tokens": 1, "reasons": []}


def test_audit_V1_V5_all_true(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    ef = entry("ep:a.py::f", "a.py", "h1")
    ctx = assemble_vam_coder(
        ws, [_dec("ep:a.py::f", "REUSE_KV")], {"ep:a.py::f": ef},
        {"ep:a.py::f": "h1"},
    )
    a = ctx.assemble_audit[0]
    assert a["verified_safe_omission"] is True
    assert a["omitted_bytes"] > 0
    assert a["omitted_tokens_est"] > 0
    assert ctx.n_verified_safe_omissions == 1


def test_audit_same_file_expand_not_omission(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "m.py").write_text("def f():\n    return 1\n\ndef g():\n    return 2\n",
                             encoding="utf-8")
    ef = entry("ep:m.py::f", "m.py", "h1")
    eg = entry("ep:m.py::g", "m.py", "h2")
    ctx = assemble_vam_coder(
        ws,
        [_dec("ep:m.py::f", "REUSE_KV"), _dec("ep:m.py::g", "EXPAND")],
        {"ep:m.py::f": ef, "ep:m.py::g": eg},
        {"ep:m.py::f": "h1"},
    )
    a = ctx.assemble_audit[0]
    assert a["verified_safe_omission"] is False
    assert a["omitted_bytes"] == 0
    assert a["omitted_tokens_est"] == 0
    assert a["included"] is True
    assert ctx.n_verified_safe_omissions == 0


def test_audit_never_sent_step1(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    ef = entry("ep:a.py::f", "a.py", "h1")
    ctx = assemble_vam_coder(
        ws, [_dec("ep:a.py::f", "REUSE_KV")], {"ep:a.py::f": ef}, {}
    )
    a = ctx.assemble_audit[0]
    assert a["previously_sent"] is False
    assert a["verified_safe_omission"] is False
    assert a["omitted_bytes"] == 0
    assert ctx.n_verified_safe_omissions == 0


def test_redact_replaces_file_blocks_only_in_assistant():
    msgs = [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "FILE: not_redacted.py\n```python\nx=1\n```"},
        {"role": "assistant",
         "content": "FILE: a.py\n```python\ndef f():\n    return 1\n```\nNO_EDIT or notes"},
        {"role": "assistant", "content": "error: MODEL_HTTP_ERROR"},
    ]
    out = redact_assistant_code(msgs)
    assert "FILE: a.py [redacted," in out[2]["content"]
    assert "def f()" not in out[2]["content"]
    assert "NO_EDIT or notes" in out[2]["content"]
    assert out[1]["content"] == msgs[1]["content"]  # user 不变
    assert out[0]["content"] == "SYS"
    assert out[3]["content"] == "error: MODEL_HTTP_ERROR"


def test_history_code_metrics():
    history = [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "task"},
        {"role": "assistant",
         "content": "FILE: a.py\n```python\nabcd\n```\nFILE: b.py\n```python\nefghij\n```"},
    ]
    m = history_code_metrics(history)
    assert m["history_file_blocks"] == 2
    assert m["history_code_chars"] == len("abcd\n") + len("efghij\n")


def test_match_event_and_absence():
    ev = [{"event": "content_stale", "symbol_id": "ep:tax.py::tax_rate"}]
    assert match_event(
        {"kind": "invalidation", "event": "content_stale",
         "target_file": "tax.py", "target_symbol": "tax_rate"}, ev
    )
    assert not match_event(
        {"kind": "invalidation", "event": "content_stale",
         "target_file": "tax.py", "target_symbol": "other"}, ev
    )
    assert match_event(
        {"kind": "absence", "event": "any",
         "target_file": "tax.py", "target_symbol": "*"}, ev
    )


def test_slice_invalidation(tmp_path):
    log = tmp_path / "inv.jsonl"
    rows = [
        {"event": "insert", "symbol_id": "ep:a.py::f"},
        {"event": "sync_completed"},
        {"event": "content_stale", "symbol_id": "ep:a.py::f"},
        {"event": "sync_completed"},
    ]
    log.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    by = slice_invalidation_by_step(log)
    assert [e["event"] for e in by["step1"]] == ["insert"]
    assert [e["event"] for e in by["step2"]] == ["content_stale"]


def _write_min_run(tmp_path, events_step2, n_omit_step2=0):
    run = tmp_path / "run"
    vam = run / "episodes" / "v1_X" / "vam_coder"
    logs = vam / "logs"
    logs.mkdir(parents=True)
    lines = [{"event": "insert", "symbol_id": "ep:a.py::f"},
             {"event": "sync_completed"}]
    lines.extend(events_step2)
    lines.append({"event": "sync_completed"})
    (logs / "invalidation_events.jsonl").write_text(
        "\n".join(json.dumps(x) for x in lines), encoding="utf-8"
    )
    for step, n in (("step1", 0), ("step2", n_omit_step2)):
        sd = vam / "steps" / step
        sd.mkdir(parents=True)
        (sd / "result.json").write_text(
            json.dumps({"n_verified_safe_omissions": n}), encoding="utf-8"
        )
    return run


def test_q3a_conjunctive_missing_unverified_fails(tmp_path):
    pre = {
        "entries": [
            {"task_id": "v1_X", "step": "step2", "kind": "invalidation",
             "event": "content_stale", "target_file": "a.py",
             "target_symbol": "f", "required": True},
            {"task_id": "v1_X", "step": "step2", "kind": "invalidation",
             "event": "dependent_unverified", "target_file": "b.py",
             "target_symbol": "g", "required": True},
        ]
    }
    pp = tmp_path / "pre.json"
    pp.write_text(json.dumps(pre), encoding="utf-8")
    run = _write_min_run(
        tmp_path, [{"event": "content_stale", "symbol_id": "ep:a.py::f"}]
    )
    out = check_run(run, pp, None)
    task = out["tasks"][0]
    assert task["q3a_q3b_pass"] is False
    assert out["all_required_passed"] is False


def test_q3a_pass_when_all_required_and_opt_missing(tmp_path):
    pre = {
        "entries": [
            {"task_id": "v1_X", "step": "step2", "kind": "invalidation",
             "event": "content_stale", "target_file": "a.py",
             "target_symbol": "f", "required": True},
            {"task_id": "v1_X", "step": "step2", "kind": "invalidation",
             "event": "insert", "target_file": "c.py",
             "target_symbol": "new_fn", "required": False},
        ]
    }
    pp = tmp_path / "pre.json"
    pp.write_text(json.dumps(pre), encoding="utf-8")
    run = _write_min_run(
        tmp_path, [{"event": "content_stale", "symbol_id": "ep:a.py::f"}]
    )
    out = check_run(run, pp, None)
    assert out["all_required_passed"] is True


def test_q3b_min_count(tmp_path):
    pre = {
        "entries": [
            {"task_id": "v1_X", "step": "step2", "kind": "omission",
             "event": "safe_omission", "target_file": "stable_a.py;stable_b.py",
             "target_symbol": "*", "required": True, "min_count": 2},
        ]
    }
    pp = tmp_path / "pre.json"
    pp.write_text(json.dumps(pre), encoding="utf-8")
    run = _write_min_run(tmp_path, [], n_omit_step2=1)
    out = check_run(run, pp, None)
    assert out["all_required_passed"] is False
    run2 = _write_min_run(tmp_path / "b", [], n_omit_step2=2)
    out2 = check_run(run2, pp, None)
    assert out2["all_required_passed"] is True


def test_predecl_hash_mismatch_refused(tmp_path):
    pre = {"entries": []}
    pp = tmp_path / "pre.json"
    pp.write_text(json.dumps(pre), encoding="utf-8")
    run = _write_min_run(tmp_path, [])
    live = sha256_file(pp)
    try:
        check_run(run, pp, "deadbeef")
        assert False, "should SystemExit on hash mismatch"
    except SystemExit as e:
        assert "MISMATCH" in str(e)
    # 正确哈希可通过
    out = check_run(run, pp, live)
    assert out["predeclared_sha256"] == live


def test_csv_has_audit_columns():
    assert "n_verified_safe_omissions" in CSV_FIELDS
    assert "history_file_blocks" in CSV_FIELDS


def test_manifest_refuse_overwrite(tmp_path):
    import subprocess
    name = "p1_test_manifest_refuse"
    target = P1_ROOT / "manifests" / f"{name}.json"
    if target.exists():
        target.unlink()
    p1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "make_manifest.py"), "--name", name],
        capture_output=True, text=True, cwd=str(P1_ROOT.parent),
        encoding="utf-8", errors="replace",
    )
    assert p1.returncode == 0, p1.stderr
    assert target.is_file()
    p2 = subprocess.run(
        [sys.executable, str(SCRIPTS / "make_manifest.py"), "--name", name],
        capture_output=True, text=True, cwd=str(P1_ROOT.parent),
        encoding="utf-8", errors="replace",
    )
    assert p2.returncode == 2
    target.unlink()
