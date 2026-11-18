"""M3-FIX-01：请求前 INSUFFICIENT 门闩 — 必须断言 chat 调用次数。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_p1_v12 as rp  # noqa: E402
from run_p1_v12 import should_call_model  # noqa: E402
from v11.visibility import content_sha256  # noqa: E402
from v12.assemble import assemble_v12  # noqa: E402
from v12.config import load_arm  # noqa: E402
from v12.levels import ExpandPlan, FileLevel, build_plan  # noqa: E402
from v12.messages_visibility import verify_omissions_in_messages  # noqa: E402
from v12.proof import tracker_from_history  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402
from p1_common import SYSTEM_PROMPT, build_messages  # noqa: E402


class _FakeChat:
    def __init__(self):
        self.n = 0

    def __call__(self, *a, **k):
        self.n += 1
        return SimpleNamespace(
            text="NO_EDIT",
            prompt_tokens=10,
            completion_tokens=1,
            latency_ms=1.0,
            usage_source="api",
            error=None,
            raw_usage={},
        )


def _ctx_insufficient(reasons=None):
    return SimpleNamespace(insufficient=True, insufficient_reasons=reasons or ["X"])


def _ctx_ok():
    return SimpleNamespace(insufficient=False, insufficient_reasons=[])


def _check(ok=True, miss=None):
    return SimpleNamespace(
        ok=ok,
        missing_or_mismatch=miss or [],
        edit_target_full_verified=ok,
        candidate_full_verified=ok,
    )


# --- 单元：门闩 ---
def test_should_call_ok():
    allow, reason = should_call_model(_ctx_ok(), _check(True))
    assert allow and reason == ""


def test_should_call_insufficient_blocks():
    allow, reason = should_call_model(
        _ctx_insufficient(["EDIT_TARGET_FULL_VERIFY_FAIL:a.py"]), _check(True)
    )
    assert not allow
    assert "INSUFFICIENT" in reason


def test_should_call_check_fail_blocks():
    allow, reason = should_call_model(_ctx_ok(), _check(False, ["a.py"]))
    assert not allow


# --- 集成：mock chat_completion 次数 ---
def _minimal_episode(ep_id="v1_IRR01"):
    return {
        "id": ep_id,
        "steps": [
            {"id": "step1", "instruction": "只修改 alpha.py：a() 返回 10。", "eval": "eval/step1"},
            {"id": "step2", "instruction": "只新增 alpha.py 的 a2() 返回 a()+1。不要修改 beta.py。", "eval": "eval/step2"},
        ],
    }


def _run_one(tmp_path, monkeypatch, fake_chat, fake_eval=None, **kwargs):
    monkeypatch.setattr(rp, "chat_completion", fake_chat)
    if fake_eval is not None:
        monkeypatch.setattr(rp, "run_eval", fake_eval)
    else:
        monkeypatch.setattr(rp, "run_eval", lambda *a, **k: (True, "passed"))
    out = tmp_path / "out"
    cfg = rp.AppConfig.load(rp.PROJECT_ROOT / "config" / "default.json")
    args = SimpleNamespace(
        dry_run=False,
        pause_seconds=0,
        max_history_chars=24000,
        temperature=0.0,
        seed=0,
        max_tokens=64,
        timeout=5.0,
        eval_timeout=5.0,
        mode_banner="short",
        closure_depth=2,
        budget_tokens=4096,
        context_window=8192,
    )
    rows, summary = rp.run_episode_arm(
        episode=_minimal_episode(),
        arm=kwargs.get("arm", "E"),
        out_dir=out,
        model="mock-model",
        endpoint="http://127.0.0.1:9/v1",
        args=args,
        cfg=cfg,
        rep=1,
    )
    return rows, summary, out


def test_integration_pass_allows_chat(tmp_path, monkeypatch):
    fake = _FakeChat()
    rows, _, out = _run_one(tmp_path, monkeypatch, fake)
    # IRR01 E step2 现应强制 alpha FULL → verify 通过 → 允许请求
    assert fake.n >= 1
    # 至少 step1 允许；step2 也应允许
    assert fake.n == 2
    psc = json.loads(
        (out / "episodes/v1_IRR01/vam_coder_v1.2_E/steps/step2/pre_send_check.json").read_text()
    )
    assert psc["ok"] is True
    assert psc["edit_target_full_verified"] is True


def test_integration_force_full_recover_allows_chat(tmp_path, monkeypatch):
    """首次 verify 失败 → force_full 后通过 → 仍允许请求（次数=步数）。"""
    real_verify = rp.verify_omissions_in_messages
    calls = {"n": 0}

    def flaky_verify(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            # 首次：伪造失败
            r = real_verify(*a, **k)
            r.ok = False
            r.missing_or_mismatch = list(r.missing_or_mismatch) + ["__fake__"]
            r.edit_target_full_verified = False
            return r
        return real_verify(*a, **k)

    monkeypatch.setattr(rp, "verify_omissions_in_messages", flaky_verify)
    fake = _FakeChat()
    rows, _, out = _run_one(tmp_path, monkeypatch, fake)
    assert calls["n"] >= 2
    assert fake.n == 2  # force_full 后恢复 → 允许
    psc = json.loads(
        (out / "episodes/v1_IRR01/vam_coder_v1.2_E/steps/step1/pre_send_check.json").read_text()
    )
    assert psc["revised"] is True


def test_integration_second_fail_chat_count_zero(tmp_path, monkeypatch):
    """二次仍失败 → chat 调用次数必须为 0。"""
    bad = SimpleNamespace(
        ok=False,
        missing_or_mismatch=["alpha.py"],
        reasons={"alpha.py": "not_in_current_context"},
        visible_hashes={},
        edit_target_full_verified=False,
        candidate_full_verified=True,
        edit_target_missing=["alpha.py"],
        candidate_missing=[],
    )
    monkeypatch.setattr(rp, "verify_omissions_in_messages", lambda *a, **k: bad)
    fake = _FakeChat()
    rows, _, out = _run_one(tmp_path, monkeypatch, fake)
    assert fake.n == 0
    for step in ("step1", "step2"):
        psc_path = (
            out / "episodes/v1_IRR01/vam_coder_v1.2_E/steps" / step / "pre_send_check.json"
        )
        assert psc_path.exists()
        psc = json.loads(psc_path.read_text())
        assert psc["ok"] is False
        assert psc["edit_target_full_verified"] is False
        res = json.loads(
            (out / "episodes/v1_IRR01/vam_coder_v1.2_E/steps" / step / "result.json").read_text()
        )
        assert "INSUFFICIENT" in (res.get("error") or "")
        # 审计完整
        audit = (
            out / "episodes/v1_IRR01/vam_coder_v1.2_E/logs/injection_audit.jsonl"
        )
        assert audit.exists() and audit.stat().st_size > 0


def test_integration_edit_target_fail_chat_zero(tmp_path, monkeypatch):
    """E 在 current context 缺失 → 调用次数 0。"""
    def et_fail(messages, omitted, disk_sha, **k):
        r = verify_omissions_in_messages(
            messages,
            omitted,
            disk_sha,
            edit_targets=k.get("edit_targets"),
            candidate_full=k.get("candidate_full"),
        )
        # 强制 E 失败
        r.ok = False
        r.edit_target_full_verified = False
        r.edit_target_missing = list(r.edit_target_missing or []) + ["alpha.py"]
        r.missing_or_mismatch = list(r.missing_or_mismatch) + ["alpha.py"]
        r.reasons = dict(r.reasons or {})
        r.reasons["alpha.py"] = "not_in_current_context"
        return r

    monkeypatch.setattr(rp, "verify_omissions_in_messages", et_fail)
    fake = _FakeChat()
    _run_one(tmp_path, monkeypatch, fake)
    assert fake.n == 0


def test_integration_candidate_fail_chat_zero(tmp_path, monkeypatch):
    def cf_fail(messages, omitted, disk_sha, **k):
        r = verify_omissions_in_messages(
            messages, omitted, disk_sha,
            edit_targets=k.get("edit_targets"),
            candidate_full=k.get("candidate_full") or ["ghost_cand.py"],
        )
        r.ok = False
        r.candidate_full_verified = False
        r.candidate_missing = ["ghost_cand.py"]
        r.missing_or_mismatch = list(r.missing_or_mismatch) + ["ghost_cand.py"]
        return r

    monkeypatch.setattr(rp, "verify_omissions_in_messages", cf_fail)
    fake = _FakeChat()
    _run_one(tmp_path, monkeypatch, fake)
    assert fake.n == 0


def test_integration_missing_required_chat_zero(tmp_path, monkeypatch):
    """缺必须文件：assemble 后 insufficient → 调用次数 0。"""
    real_asm = rp.assemble_v12

    def asm_missing(*a, **k):
        ctx = real_asm(*a, **k)
        ctx.insufficient = True
        ctx.insufficient_reasons = list(ctx.insufficient_reasons) + [
            "MISSING_REQUIRED_FILE"
        ]
        return ctx

    monkeypatch.setattr(rp, "assemble_v12", asm_missing)
    fake = _FakeChat()
    rows, _, out = _run_one(tmp_path, monkeypatch, fake)
    assert fake.n == 0
    res = json.loads(
        (out / "episodes/v1_IRR01/vam_coder_v1.2_E/steps/step1/result.json").read_text()
    )
    assert "INSUFFICIENT" in (res.get("error") or "")
    assert (out / "episodes/v1_IRR01/vam_coder_v1.2_E/steps/step1/pre_send_check.json").exists()


def test_dry_run_insufficient_skips_without_chat(tmp_path, monkeypatch):
    fake = _FakeChat()
    monkeypatch.setattr(rp, "chat_completion", fake)

    def bad_verify(*a, **k):
        return SimpleNamespace(
            ok=False,
            missing_or_mismatch=["x"],
            reasons={"x": "not_in_current_context"},
            visible_hashes={},
            edit_target_full_verified=False,
            candidate_full_verified=True,
            edit_target_missing=["x"],
            candidate_missing=[],
        )

    monkeypatch.setattr(rp, "verify_omissions_in_messages", bad_verify)
    monkeypatch.setattr(rp, "run_eval", lambda *a, **k: (True, "ok"))
    out = tmp_path / "dry"
    cfg = rp.AppConfig.load(rp.PROJECT_ROOT / "config" / "default.json")
    args = SimpleNamespace(
        dry_run=True, pause_seconds=0, max_history_chars=24000,
        temperature=0.0, seed=0, max_tokens=64, timeout=5.0, eval_timeout=5.0,
        mode_banner="short", closure_depth=2, budget_tokens=4096, context_window=8192,
    )
    rows = rp.run_episode_arm(
        episode=_minimal_episode(), arm="E", out_dir=out,
        model="m", endpoint="http://x", args=args, cfg=cfg, rep=1,
    )
    if isinstance(rows, tuple):
        rows = rows[0]
    assert fake.n == 0
    assert all("INSUFFICIENT" in (r.get("error") or "") for r in rows)
