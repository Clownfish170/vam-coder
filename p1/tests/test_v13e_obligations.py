"""V13E·S2 义务账本 v2：窄口径解析、未结判定、紧凑渲染与成本上界。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from p1_common import build_messages  # noqa: E402
from v12.obligations import (  # noqa: E402
    is_open,
    open_lines,
    parse_obligation,
    raise_sha,
    render_line,
)

TAX = "RATE = 0.1\n"
BIZ = "def gross(x):\n    return x\n"


class TestParse:
    def test_modify_existing_symbol(self):
        o = parse_obligation(
            3, "请参考 taxrate.py 中的 RATE 定义。修改 biz.py 中的 gross(x)：返回 x * 2。不要修改 taxrate.py。"
        )
        assert o.kind == "modify"
        assert ("biz.py", "gross") in o.targets
        # 「不要修改」子句不得产生目标
        assert all(f != "taxrate.py" for f, _ in o.targets)

    def test_add_symbol(self):
        o = parse_obligation(4, "codec.py 新增 encode2(kind, body, tag) 与 decode2(text)。")
        assert o.kind == "add"
        assert ("codec.py", "encode2") in o.targets

    def test_unparseable_is_raw(self):
        o = parse_obligation(2, "把整体行为调整得更稳健一些。")
        assert o.kind == "raw"
        assert o.targets == []
        assert render_line(o).startswith("[2] ")


class TestOpenClosed:
    def test_add_open_until_symbol_present(self):
        o = raise_sha(parse_obligation(1, "codec.py 新增 encode2(text)。"), {})
        files = {"codec.py": "def decode():\n    pass\n"}
        assert is_open(o, files, {"codec.py": "h1"}) is True
        files = {"codec.py": "def encode2(text):\n    return 1\n"}
        assert is_open(o, files, {"codec.py": "h1"}) is False

    def test_modify_open_until_file_edited(self):
        o = raise_sha(
            parse_obligation(1, "修改 biz.py 中的 gross(x) 返回 x*2。"),
            {"biz.py": "h_raise"},
        )
        assert is_open(o, {"biz.py": BIZ}, {"biz.py": "h_raise"}) is True
        assert is_open(o, {"biz.py": BIZ}, {"biz.py": "h_changed"}) is False

    def test_raw_always_open(self):
        o = parse_obligation(1, "让整体更稳健。")
        assert is_open(o, {}, {}) is True

    def test_missing_sha_at_raise_is_conservatively_open(self):
        # 提出时文件不存在（新建类）→ 保守未结
        o = raise_sha(parse_obligation(1, "修改 newmod.py 中的 f(x) 返回 1。"), {})
        assert o.kind == "modify"
        assert is_open(o, {"newmod.py": "def f(x):\n    return 1\n"}, {"newmod.py": "h"}) is True


class TestRenderingAndCost:
    def test_lines_are_compact(self):
        o = parse_obligation(
            3, "请参考 taxrate.py 中的 RATE 定义。修改 biz.py 中的 gross(x)：返回 x * (1 + RATE) * 2（翻倍）。不要修改 taxrate.py。"
        )
        line = render_line(o)
        assert line == "[3] 修改 biz.py: gross"
        assert len(line) < 40  # v1 为指令全文（79+ 字符）

    def test_open_lines_filters_closed(self):
        a = raise_sha(parse_obligation(1, "修改 biz.py 中的 gross(x) 返回 1。"), {"biz.py": "h0"})
        b = raise_sha(parse_obligation(2, "codec.py 新增 encode2(t)。"), {})
        files = {"biz.py": BIZ, "codec.py": "def encode2(t):\n    return 1\n"}
        sha = {"biz.py": "h0", "codec.py": "h2"}  # biz 未再改 → 仍开；encode2 已在 → 关
        lines = open_lines([a, b], files, sha)
        assert lines == ["[1] 修改 biz.py: gross"]

    def test_raw_line_capped(self):
        o = parse_obligation(1, "这是一段非常长的、没有可解析目标的说明" * 4)
        line = render_line(o)
        assert len(line) <= 3 + 1 + 48 + 1  # "[1] " + cap + …
        assert line.endswith("…")

    def test_ledger_cheap_in_user_message(self):
        """账本段必须显著小于 v1 的指令全文形态。"""
        instrs = [
            "请参考 taxrate.py 中的 RATE 定义。修改 biz.py 中的 gross(x)：返回 x * (1 + RATE) * 2（翻倍）。不要修改 taxrate.py。",
            "请参考 biz.py 当前实现。修改 taxrate.py 中 RATE 为 0.25（当前 0.1）。不要修改 biz.py。",
        ]
        obs = [
            raise_sha(parse_obligation(i + 1, t), {"biz.py": "h", "taxrate.py": "h"})
            for i, t in enumerate(instrs)
        ]
        # 全部未结（提出后哈希未变 + RATE 常量型目标）
        files = {"biz.py": BIZ, "taxrate.py": TAX}
        sha = {"biz.py": "h", "taxrate.py": "h"}
        lines = open_lines(obs, files, sha)
        assert lines, "testprecondition: 至少一条未结"
        with_led = build_messages([], "t", "CTX", ledger_lines=lines)[-1]["content"]
        v1 = build_messages([], "t", "CTX", ledger_lines=instrs)[-1]["content"]
        seg = lambda s: s[s.index("=== OBLIGATIONS ===") : s.index("=== CONTEXT ===")]  # noqa: E731
        assert len(seg(with_led)) < 0.5 * len(seg(v1))
