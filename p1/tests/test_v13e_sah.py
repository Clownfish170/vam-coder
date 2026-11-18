"""V13E·SAH 回归测试：状态投影的 O′ 等价性 + 义务账本的消息结构。

核心断言（设计稿 §3）：投影前后 `full_files_in_messages` / `tracker_from_history`
/ `verify_omissions_in_messages` 逐字段相等 —— 投影不得改变任何安全判定。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from p1_common import build_messages  # noqa: E402
from v11.visibility import content_sha256  # noqa: E402
from v12.config import config_diff, load_arm  # noqa: E402
from v12.history_project import fold_marker, project_history  # noqa: E402
from v12.messages_visibility import (  # noqa: E402
    _ASSIST_FILE_RE,
    _CTX_FILE_RE,
    current_context_files,
    full_files_in_messages,
    verify_omissions_in_messages,
)
from v12.proof import tracker_from_history  # noqa: E402

BODY_V1 = "def fa():\n    return 1\n"
BODY_V2 = "def fa():\n    return 2\n"
BODY_B = "def fb():\n    return 3\n"


def _asst(text: str) -> dict:
    return {"role": "assistant", "content": text}


def _history_multi() -> list[dict]:
    """多文件、多版本、含多块消息与非 FILE 消息的合成历史。"""
    return [
        {"role": "system", "content": "SYS"},
        _asst("FILE: a.py\n```python\n" + BODY_V1 + "```\n"),
        _asst("FILE: b.py\n```python\n" + BODY_B + "```\n"),
        _asst(""),  # 空响应
        _asst("FILE: a.py\n```python\n" + BODY_V2 + "```\n"),
        _asst("NO_EDIT"),
        _asst(
            "FILE: a.py\n```python\n" + BODY_V2 + "```\n"
            "FILE: b.py\n```python\n" + BODY_B + "```\n"
        ),
    ]


class TestProjectionEquivalence:
    def test_full_files_extract_equal(self):
        hist = _history_multi()
        proj, stats = project_history(hist)
        assert full_files_in_messages(proj) == full_files_in_messages(hist)
        assert stats["folded_blocks"] >= 2  # a.py 早版本 + 末条消息里重复的 a.py
        assert stats["kept_blocks"] >= 1

    def test_tracker_and_presend_equal(self):
        hist = _history_multi()
        proj, _ = project_history(hist)
        disk = {"a.py": BODY_V2, "b.py": BODY_B}
        disk_sha = {k: content_sha256(v) for k, v in disk.items()}
        tr_h = tracker_from_history(hist)
        tr_p = tracker_from_history(proj)
        assert tr_h.snapshot() == tr_p.snapshot()
        assert tr_h.visible_paths() == tr_p.visible_paths()

        user_ctx = "--- FILE a.py (full current source) ---\n" + BODY_V2
        for pool in (hist, proj):
            messages = build_messages(pool, "修改 fa", user_ctx)
            check = verify_omissions_in_messages(
                messages, ["b.py"], disk_sha, edit_targets=["a.py"]
            )
            assert check.ok
            # 字段级全等
            if pool is hist:
                ref = check
            else:
                assert check.ok == ref.ok
                assert check.missing_or_mismatch == ref.missing_or_mismatch
                assert check.reasons == ref.reasons
                assert check.visible_hashes == ref.visible_hashes
                assert check.edit_target_full_verified == ref.edit_target_full_verified

    def test_omission_fails_identically_without_last_block(self):
        """若某文件在历史中完全不可见，投影前后都必须以同一理由失败。"""
        hist = [
            {"role": "system", "content": "SYS"},
            _asst("FILE: a.py\n```python\n" + BODY_V1 + "```\n"),
        ]
        proj, _ = project_history(hist)
        disk_sha = {"gone.py": content_sha256("x = 1\n"), "a.py": content_sha256(BODY_V1)}
        results = []
        for pool in (hist, proj):
            messages = build_messages(pool, "t", "--- FILE a.py (full current source) ---\n" + BODY_V1)
            results.append(
                verify_omissions_in_messages(messages, ["gone.py"], disk_sha)
            )
        assert results[0].ok is False and results[1].ok is False
        assert results[0].missing_or_mismatch == results[1].missing_or_mismatch
        assert results[0].reasons == results[1].reasons

    def test_fold_marker_not_matched_and_bodies_clean(self):
        hist = _history_multi()
        proj, _ = project_history(hist)
        assert fold_marker("a.py") in proj[1]["content"]
        # 投影后提取出的 body 不得含折叠标记，且仍只含末版本
        for path, body in full_files_in_messages(proj).items():
            assert "历史折叠" not in body
        # 每条消息内每个路径至多剩一个完整块
        for m in proj:
            if m.get("role") != "assistant":
                continue
            seen: list[str] = []
            for mo in _ASSIST_FILE_RE.finditer(m.get("content") or ""):
                seen.append(mo.group("path"))
            assert len(seen) == len(set(seen)), seen
        assert full_files_in_messages(proj)["a.py"].strip() == BODY_V2.strip()

    def test_non_assistant_and_system_untouched(self):
        hist = _history_multi()
        proj, _ = project_history(hist)
        assert proj[0] is hist[0]  # system 原样（同一对象）
        # 首个 a.py 块被折叠为标记（正则止于 ```，其后换行保留）；末消息中的 a/b 是全局最后出现 → 保留
        assert proj[1]["content"] == fold_marker("a.py") + "\n"
        assert proj[4]["content"] == fold_marker("a.py") + "\n"
        assert proj[6]["content"].endswith("```\n")
        assert "FILE: a.py" in proj[6]["content"]
        # 空/NO_EDIT 消息原样
        assert proj[3] is hist[3]
        assert proj[5] is hist[5]

    def test_history_without_file_blocks_unchanged(self):
        hist = [{"role": "system", "content": "S"}, _asst("NO_EDIT"), _asst("plain")]
        proj, stats = project_history(hist)
        assert proj == hist
        assert stats["folded_blocks"] == 0

    def test_idempotent(self):
        hist = _history_multi()
        once, _ = project_history(hist)
        twice, stats2 = project_history(once)
        assert twice == once
        assert stats2["folded_blocks"] == 0


class TestProjectModes:
    """first_last 档：保首版+末版、折中间版，且 O′ 等价性同样成立。"""

    def _multi_version_history(self) -> list[dict]:
        return [
            {"role": "system", "content": "SYS"},
            _asst("FILE: a.py\n```python\n" + BODY_V1 + "```\n"),  # v1（首）
            _asst("FILE: a.py\n```python\nV2 = 2\n```\n"),  # v2（中）
            _asst("FILE: b.py\n```python\n" + BODY_B + "```\n"),
            _asst("FILE: a.py\n```python\n" + BODY_V2 + "```\n"),  # v3（末）
        ]

    def test_first_last_keeps_endpoints_folds_middle(self):
        hist = self._multi_version_history()
        proj, stats = project_history(hist, "first_last")
        assert stats["folded_blocks"] == 1  # 只折 v2
        content = "\n".join(m.get("content") or "" for m in proj)
        assert BODY_V1 in content  # 首版保留
        assert BODY_V2 in content  # 末版保留
        assert "V2 = 2" not in content  # 中间版折叠
        assert fold_marker("a.py", "first_last") in content

    def test_first_last_equivalence(self):
        hist = self._multi_version_history()
        proj, _ = project_history(hist, "first_last")
        assert full_files_in_messages(proj) == full_files_in_messages(hist)
        # 后写覆盖 → 末版哈希仍是提取结果
        assert full_files_in_messages(proj)["a.py"].strip() == BODY_V2.strip()

    def test_first_last_saves_less_than_last(self):
        hist = self._multi_version_history()
        _, s_last = project_history(hist, "last")
        _, s_fl = project_history(hist, "first_last")
        assert s_fl["folded_blocks"] < s_last["folded_blocks"]
        assert s_fl["chars_after"] > s_last["chars_after"]
        assert s_fl["chars_after"] <= s_fl["chars_before"]

    def test_single_occurrence_never_folded_in_either_mode(self):
        hist = self._multi_version_history()
        for mode in ("last", "first_last"):
            proj, stats = project_history(hist, mode)
            content = "\n".join(m.get("content") or "" for m in proj)
            assert BODY_B in content, mode  # b.py 只出现一次
            assert full_files_in_messages(proj) == full_files_in_messages(hist)

    def test_bad_mode_rejected(self):
        import pytest

        with pytest.raises(ValueError):
            project_history([], "middle")

    def test_runner_reads_mode_from_args(self):
        src = (ROOT / "run_p1_v12.py").read_text(encoding="utf-8")
        assert 'sah_project_mode=getattr(args, "sah_project_mode", "last")' in src
        assert "project_history(\n" in src and "sah_project_mode" in src


class TestObligationLedger:
    CTX = "--- FILE a.py (full current source) ---\n" + BODY_V1

    def test_default_output_byte_identical(self):
        hist = _history_multi()
        legacy = (
            "=== TASK ===\ntask\n\n"
            "=== CONTEXT ===\n" + self.CTX.strip() + "\n\n"
            "=== OUTPUT FORMAT ===\n"
            "Respond only with FILE: blocks (or NO_EDIT)."
        )
        assert build_messages(hist, "task", self.CTX)[-1]["content"] == legacy
        assert (
            build_messages(hist, "task", self.CTX, ledger_lines=None)[-1]["content"]
            == legacy
        )
        assert (
            build_messages(hist, "task", self.CTX, ledger_lines=[])[-1]["content"]
            == legacy
        )

    def test_ledger_position_and_structure(self):
        out = build_messages(
            _history_multi(),
            "本步任务",
            self.CTX,
            ledger_lines=["[1] 指令一", "[2] 指令二"],
        )
        content = out[-1]["content"]
        i_task = content.index("=== TASK ===")
        i_led = content.index("=== OBLIGATIONS ===")
        i_ctx = content.index("=== CONTEXT ===")
        i_fmt = content.index("=== OUTPUT FORMAT ===")
        assert i_task < i_led < i_ctx < i_fmt
        assert "- [1] 指令一" in content and "- [2] 指令二" in content

    def test_ledger_does_not_disturb_ctx_extraction(self):
        hist = _history_multi()
        plain = build_messages(hist, "t", self.CTX)
        with_led = build_messages(hist, "t", self.CTX, ledger_lines=["[1] 在 a.py 中改 fa"])
        # CONTEXT 段与 FILE 块提取完全一致
        p_user = plain[-1]["content"]
        w_user = with_led[-1]["content"]
        p_ctx = p_user[p_user.index("=== CONTEXT ===") :]
        w_ctx = w_user[w_user.index("=== CONTEXT ===") :]
        assert p_ctx == w_ctx
        assert current_context_files(plain) == current_context_files(with_led)
        assert [
            mo.group("body") for mo in _CTX_FILE_RE.finditer(p_user)
        ] == [mo.group("body") for mo in _CTX_FILE_RE.finditer(w_user)]
        # 账本行不得含围栏（避免被任何 FILE 提取器捕获）
        assert "```" not in w_user[w_user.index("=== OBLIGATIONS ===") : w_user.index("=== CONTEXT ===")]

    def test_instruction_text_only_no_file_body(self):
        # 账本可含指令里出现的文件名，但不得含 FILE 块标记
        out = build_messages([], "t", self.CTX, ledger_lines=["[1] 修改 a.py 的 fa 返回 2"])
        seg = out[-1]["content"]
        assert "=== OBLIGATIONS ===" in seg
        assert "--- FILE a.py (full current source) ---" in seg  # CONTEXT 段照常


class TestArmDefaults:
    def test_legacy_arms_sah_off(self):
        for arm in ("E", "F", "V13ACR", "V13BICG", "MEMORYOFF", "V13DVAD"):
            cfg = load_arm(arm)
            assert cfg.sah_project is False
            assert cfg.sah_ledger is False

    def test_new_arms_sah_on_and_flags_are_the_only_delta(self):
        proj = load_arm("V13EPROJ")
        sah = load_arm("V13ESAH")
        icg_sah = load_arm("V13ICGSAH")
        assert (proj.sah_project, proj.sah_ledger) == (True, False)
        assert (sah.sah_project, sah.sah_ledger) == (True, True)
        assert (icg_sah.sah_project, icg_sah.sah_ledger) == (True, True)
        # 与各自基座的唯一差异 = SAH 开关
        assert config_diff(load_arm("F"), proj) == {"sah_project"}
        assert config_diff(load_arm("F"), sah) == {"sah_project", "sah_ledger"}
        assert config_diff(load_arm("V13BICG"), icg_sah) == {"sah_project", "sah_ledger"}


class TestRunnerWiring:
    def test_runner_has_projection_and_ledger_hooks(self):
        src = (ROOT / "run_p1_v12.py").read_text(encoding="utf-8")
        assert "project_history(" in src
        assert "sah_project_mode" in src
        assert "ledger_lines=sah_ledger_lines" in src
        assert src.count("ledger_lines=sah_ledger_lines") >= 3
        assert '"V13ESAH"' in src and '"V13ICGSAH"' in src

    def test_vso_modules_untouched_by_sah(self):
        """SAH 不得写入 VSO 校验模块（语义零修改的护栏）。"""
        for rel in (
            "v12/messages_visibility.py",
            "v12/proof.py",
        ):
            text = (ROOT / rel).read_text(encoding="utf-8")
            assert "sah_" not in text and "project_history" not in text
