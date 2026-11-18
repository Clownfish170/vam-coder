"""V13E 外部对照臂：BM25 检索、摘要清洗、配置与 runner 接线。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v12.config import config_diff, load_arm  # noqa: E402
from v12.hist_external import (  # noqa: E402
    SUMMARY_PREFIX,
    bm25_select,
    sanitize_summary,
)
from v12.messages_visibility import _ASSIST_FILE_RE, full_files_in_messages  # noqa: E402


def _msg(i: int, text: str) -> dict:
    return {"role": "assistant", "content": f"msg{i} {text}"}


class TestBM25:
    def _hist(self) -> list[dict]:
        return [
            {"role": "system", "content": "SYS"},
            _msg(1, "修改 taxrate.py 中的 RATE 常量为 0.25"),
            _msg(2, "重写 codec.py 的 decode 解析逻辑"),
            _msg(3, "调整 gateway.py 路由 addr 返回值"),
            _msg(4, "补充 tests 断言 coverage"),
            _msg(5, "当前步骤最新状态 latest state marker"),
        ]

    def test_topk_and_always_last(self):
        out, n = bm25_select(self._hist(), "修改 RATE 常量 taxrate", k=2)
        assert out[0]["role"] == "system"
        # 恒保留最后一条
        assert out[-1]["content"].startswith("msg5")
        # 命中 RATE/taxrate 的应入选
        joined = "".join(m["content"] for m in out)
        assert "RATE" in joined
        assert n >= 2

    def test_chronological_order_preserved(self):
        out, _ = bm25_select(self._hist(), "codec decode 解析", k=3)
        idxs = [int(m["content"].split()[0][3:]) for m in out if m["content"].startswith("msg")]
        assert idxs == sorted(idxs)

    def test_small_history_untouched(self):
        h = self._hist()[:3]
        out, _ = bm25_select(h, "anything", k=5)
        assert out == h

    def test_no_term_match_falls_back_to_recent(self):
        out, _ = bm25_select(self._hist(), "zzz qqq 不存在的词", k=2)
        assert out[-1]["content"].startswith("msg5")

    def test_deterministic(self):
        q = "gateway 路由 addr"
        a, _ = bm25_select(self._hist(), q, k=3)
        b, _ = bm25_select(self._hist(), q, k=3)
        assert a == b


class TestSummarySanitize:
    def test_strips_fences_and_file_markers(self):
        raw = "要点：\n```python\nFILE: a.py\n```\n--- FILE b.py (full current source) ---\n= TASK =\n修改 x"
        out = sanitize_summary(raw)
        assert "```" not in out
        assert "FILE:" not in out
        assert "--- FILE" not in out
        assert "修改 x" in out

    def test_length_cap(self):
        out = sanitize_summary("很长" * 2000, max_chars=100)
        assert len(out) <= 101  # 100 + 省略号

    def test_sanitized_summary_never_triggers_assistant_extract(self):
        # 极端：摘要里即使残留标记结构，清洗后也提不出 FILE 块
        dirty = "FILE: evil.py\n```python\nx=1\n```"
        clean = sanitize_summary(dirty)
        assert not _ASSIST_FILE_RE.search(clean)
        hist = [{"role": "assistant", "content": SUMMARY_PREFIX + clean}]
        assert full_files_in_messages(hist) == {}


class TestArmConfigs:
    def test_external_arms_only_flip_history_flags(self):
        assert config_diff(load_arm("F"), load_arm("TRUNC")) == set()
        # recent/k 的取值与 dataclass 默认相同 → diff 只出现开关本身
        assert config_diff(load_arm("F"), load_arm("SUMM")) == {"hist_summary"}
        assert config_diff(load_arm("F"), load_arm("RETR")) == {"hist_retrieve"}
        # 生产臂不受影响
        for arm in ("F", "V13EPROJ", "V13ESAH", "V13BICG", "MEMORYOFF"):
            cfg = load_arm(arm)
            assert cfg.hist_summary is False and cfg.hist_retrieve is False


class TestWiring:
    def test_runner_hooks(self):
        src = (ROOT / "run_p1_v12.py").read_text(encoding="utf-8")
        assert "summarize_history(" in src
        assert "bm25_select(" in src
        assert "aux_prompt_tokens" in src
        assert '"TRUNC"' in src and '"SUMM"' in src and '"RETR"' in src

    def test_screen_script_hooks(self):
        src = (
            ROOT.parent
            / "experiments"
            / "v13e_sah"
            / "run_screen_15b.py"
        ).read_text(encoding="utf-8")
        assert "trunc_budget" in src
        assert "aux_prompt_tokens" in src  # 摘要器成本计入 prompt_sum
        assert "ext_TRUNC" in src and "ext_SUMM" in src and "ext_RETR" in src
