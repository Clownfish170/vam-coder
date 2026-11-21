#!/usr/bin/env python
"""V1.3-M2 Holdout 任务生成器（rev3 §2 + 原计划 §2.2 冻结类型清单）。

- 类型配额在写任务之前固定（原计划 §2.2 十二行清单）。
- 生成 project/ eval/ reference/ 与 holdout_tasks.json / holdout_manifest.json。
- 冻结前验证：eval 初态失败/参考解通过、edit target 解析符合预期、
  与 v1 24 任务文件 hash 交集为空、指令不逐字复用 v1。
- 不含模型请求；不看任何臂的实验结果。
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
V1_TASKS = P1 / "tasks"

REV3_PATH = P1 / "experiments" / "v12_p1_execution" / "v13_design" / "v13_m2_validation_plan_rev3.md"
REV3_SHA256 = "8ceed45d6554ba952a641fbbebb49b4f3eb0f69858c16ba9d58d7025eb9ee13f"

# ============================================================ 任务定义
# 每任务：
#   focus/difficulty/type：原计划 §2.2 类型（冻结，先于写任务固定）
#   files：初始 project 文件（相对路径 → 内容）
#   steps：[{instruction, eval}]  eval = eval/stepN/test_behavior.py 内容
#   expect_targets：每步预期 edit_targets（parse_edit_targets 校验）
#   ref：reference/stepN 相对初始的文件全量覆盖（累计）
# 难度分布：短4 / 中4 / 长4（原计划 §2.2）。

TASKS: list[dict] = []


def T(**kw):
    TASKS.append(kw)


# ------------------------------------------------ S01 单文件编辑（短）
T(
    id="v13_S01",
    type="single_file_edit",
    difficulty="short",
    focus="单文件编辑基线 ESR",
    files={
        "backoff.py": '''\
"""Retry backoff helpers."""


def delay(base, attempt):
    """Exponential delay in seconds."""
    return base * (2 ** attempt)


def full_delay(base, attempt):
    d = delay(base, attempt)
    return min(d, 120)
''',
        "netlog.py": '''\
"""Tiny network log helpers."""
from backoff import delay


def stamp(msg):
    return "[net] " + msg


def retry_stamp(base, attempt):
    return stamp(str(delay(base, attempt)))
''',
    },
    steps=[
        {
            "instruction": "backoff.py 中的 delay(base, attempt) 在 attempt ≥ 5 时应固定返回 30（当前仍按指数增长）。",
            "eval": '''\
import backoff


def test_cap_when_many_attempts():
    assert backoff.delay(2, 5) == 30
    assert backoff.delay(3, 7) == 30


def test_normal_exponential():
    assert backoff.delay(2, 3) == 16
    assert backoff.delay(1, 0) == 1


def test_full_delay_regression():
    assert backoff.full_delay(2, 9) == 30
''',
            "expect_targets": {"backoff.py"},
        },
        {
            "instruction": "在 backoff.py 新增 cap_half(cap)：返回 cap 的一半向下取整（int(cap/2)）。",
            "eval": '''\
import backoff


def test_cap_half():
    assert backoff.cap_half(10) == 5
    assert backoff.cap_half(5) == 2


def test_delay_regression():
    assert backoff.delay(2, 5) == 30
''',
            "expect_targets": {"backoff.py"},
        },
    ],
    ref={
        1: {
            "backoff.py": '''\
"""Retry backoff helpers."""


def delay(base, attempt):
    """Exponential delay in seconds."""
    if attempt >= 5:
        return 30
    return base * (2 ** attempt)


def full_delay(base, attempt):
    d = delay(base, attempt)
    return min(d, 120)
''',
        },
        2: {
            "backoff.py": '''\
"""Retry backoff helpers."""


def delay(base, attempt):
    """Exponential delay in seconds."""
    if attempt >= 5:
        return 30
    return base * (2 ** attempt)


def full_delay(base, attempt):
    d = delay(base, attempt)
    return min(d, 120)


def cap_half(cap):
    return int(cap / 2)
''',
        },
    },
)

# ------------------------------------------------ S02 单文件边界（短）
T(
    id="v13_S02",
    type="single_file_boundary",
    difficulty="short",
    focus="边界条件（空/负值/异常区间）",
    files={
        "tokens.py": '''\
"""Token/text counting utilities."""


def parse_n(s):
    return int(s)


def band(n):
    if n > 100:
        return "high"
    return "mid"
''',
        "reportx.py": '''\
"""Report helpers."""


def line(k, v):
    return f"{k}={v}"


def render(pairs):
    return "\n".join(line(k, v) for k, v in pairs)
''',
    },
    steps=[
        {
            "instruction": "tokens.py 中的 parse_n(s)：空白输入应返回 0，负数字符串（如 `-5`）也应返回 0（当前会抛异常或返回负值）。",
            "eval": '''\
import tokens


def test_blank_returns_zero():
    assert tokens.parse_n("") == 0
    assert tokens.parse_n("   ") == 0


def test_negative_returns_zero():
    assert tokens.parse_n("-5") == 0


def test_normal_int():
    assert tokens.parse_n("42") == 42
''',
            "expect_targets": {"tokens.py"},
        },
        {
            "instruction": "tokens.py 中的 band(n)：n<0 应返回 `low`，n==0 应返回 `zero`，n>0 应返回 `high`。",
            "eval": '''\
import tokens


def test_parse_regression():
    assert tokens.parse_n("") == 0
    assert tokens.parse_n("7") == 7


def test_band_boundaries():
    assert tokens.band(-3) == "low"
    assert tokens.band(0) == "zero"
    assert tokens.band(250) == "high"
''',
            "expect_targets": {"tokens.py"},
        },
    ],
    ref={
        1: {
            "tokens.py": '''\
"""Token/text counting utilities."""


def parse_n(s):
    if s.strip() == "":
        return 0
    v = int(s)
    if v < 0:
        return 0
    return v


def band(n):
    if n > 100:
        return "high"
    return "mid"
''',
        },
        2: {
            "tokens.py": '''\
"""Token/text counting utilities."""


def parse_n(s):
    if s.strip() == "":
        return 0
    v = int(s)
    if v < 0:
        return 0
    return v


def band(n):
    if n < 0:
        return "low"
    if n == 0:
        return "zero"
    return "high"
''',
        },
    },
)

# ------------------------------------------------ M01 双文件无强依赖（短）
T(
    id="v13_M01",
    type="multi_file_no_dep",
    difficulty="short",
    focus="Digest vs Full：相关但无依赖",
    files={
        "roll.py": '''\
"""Contact roll utilities."""

ROWS = [{"name": "ada", "team": "x"}, {"name": "bob", "team": "y"}]


def join_names(rows):
    return "|".join(r["name"] for r in rows)


def teams(rows):
    return sorted({r["team"] for r in rows})
''',
        "pretty.py": '''\
"""Formatting helpers."""


def pad(s, n):
    return s.rjust(n)


def wrap(s, width):
    return [s[i:i + width] for i in range(0, len(s), width)]
''',
    },
    steps=[
        {
            "instruction": "请修改 roll.py 中的 join_names(rows)：应以 `, `（逗号+空格）拼接各行 name（当前用 `|`）。本次不涉及 pretty.py 的排版逻辑。",
            "eval": '''\
import roll


def test_join_names_comma():
    assert roll.join_names(roll.ROWS) == "ada, bob"


def test_teams_regression():
    assert roll.teams(roll.ROWS) == ["x", "y"]
''',
            "expect_targets": {"roll.py"},
        },
        {
            "instruction": "请修改 pretty.py 中的 pad(s, n)：应右侧补空格到长度 n（当前左侧补齐）。",
            "eval": '''\
import pretty
import roll


def test_pad_right():
    assert pretty.pad("ab", 5) == "ab   "
    assert pretty.pad("ab", 2) == "ab"


def test_join_regression():
    assert roll.join_names(roll.ROWS) == "ada, bob"
''',
            "expect_targets": {"pretty.py"},
        },
    ],
    ref={
        1: {
            "roll.py": '''\
"""Contact roll utilities."""

ROWS = [{"name": "ada", "team": "x"}, {"name": "bob", "team": "y"}]


def join_names(rows):
    return ", ".join(r["name"] for r in rows)


def teams(rows):
    return sorted({r["team"] for r in rows})
''',
        },
        2: {
            "roll.py": '''\
"""Contact roll utilities."""

ROWS = [{"name": "ada", "team": "x"}, {"name": "bob", "team": "y"}]


def join_names(rows):
    return ", ".join(r["name"] for r in rows)


def teams(rows):
    return sorted({r["team"] for r in rows})
''',
            "pretty.py": '''\
"""Formatting helpers."""


def pad(s, n):
    return s.ljust(n)


def wrap(s, width):
    return [s[i:i + width] for i in range(0, len(s), width)]
''',
        },
    },
)

# ------------------------------------------------ M02 双文件弱命名相关（中）
T(
    id="v13_M02",
    type="weak_naming_ambiguity",
    difficulty="medium",
    focus="指令歧义：同名符号跨两文件",
    files={
        "stream.py": '''\
"""Message stream helpers."""


def dedupe(msgs):
    return sorted(set(msgs))


def head(msgs, n=3):
    return msgs[:n]
''',
        "stream_rules.py": '''\
"""Rule definitions for streams."""


def dedupe(msgs):
    seen = []
    for m in msgs:
        if m not in seen:
            seen.append(m)
    return seen


def normalize(msgs):
    return msgs
''',
    },
    steps=[
        {
            "instruction": "请修改 dedupe(msgs)：应保留首次出现顺序去重（当前实现先排序再去重）。",
            "eval": '''\
from stream import dedupe


def test_order_preserved():
    assert dedupe(["b", "a", "b", "c"]) == ["b", "a", "c"]


def test_numeric_input():
    assert dedupe([1, 1, 2]) == [1, 2]
''',
            "expect_targets": {"stream.py", "stream_rules.py"},
        },
        {
            "instruction": "stream_rules.py 中的 normalize(msgs) 应将字符串元素转小写（当前原样返回）。",
            "eval": '''\
from stream import dedupe
from stream_rules import normalize


def test_normalize_lower():
    assert normalize(["A", "Bc"]) == ["a", "bc"]


def test_normalize_non_string():
    assert normalize([1]) == [1]


def test_dedupe_regression():
    assert dedupe(["b", "a", "b"]) == ["b", "a"]
''',
            "expect_targets": {"stream_rules.py"},
        },
    ],
    ref={
        1: {
            "stream.py": '''\
"""Message stream helpers."""


def dedupe(msgs):
    out = []
    for m in msgs:
        if m not in out:
            out.append(m)
    return out


def head(msgs, n=3):
    return msgs[:n]
''',
        },
        2: {
            "stream.py": '''\
"""Message stream helpers."""


def dedupe(msgs):
    out = []
    for m in msgs:
        if m not in out:
            out.append(m)
    return out


def head(msgs, n=3):
    return msgs[:n]
''',
            "stream_rules.py": '''\
"""Rule definitions for streams."""


def dedupe(msgs):
    seen = []
    for m in msgs:
        if m not in seen:
            seen.append(m)
    return seen


def normalize(msgs):
    return [m.lower() if isinstance(m, str) else m for m in msgs]
''',
        },
    },
)

# ------------------------------------------------ D01 显式 import 依赖（中）
T(
    id="v13_D01",
    type="explicit_import_dep",
    difficulty="medium",
    focus="dependency_touch：显式 import 提供方",
    files={
        "geo.py": '''\
"""Geometry helpers."""
from units import MARGIN


def area(w, h):
    return w * h


def border_area(w, h):
    return (w + MARGIN) * (h + MARGIN)


def padded_area(w, h):
    return w * h
''',
        "units.py": '''\
"""Unit and margin settings."""

SCALE = 100
MARGIN = 0.1


def unit_name():
    return "m"
''',
        "notes.py": '''\
"""Field notes (unrelated)."""


def tag(s):
    return "note:" + s


def lines(text):
    return text.splitlines()
''',
    },
    steps=[
        {
            "instruction": "请修改 geo.py 中的 padded_area(w, h)：面积应乘以 (1 + MARGIN)（当前直接返回 w*h）。MARGIN 的当前取值以 units.py 为准。",
            "eval": '''\
import geo


def test_padded_area_uses_margin():
    assert abs(geo.padded_area(10, 10) - 110.0) < 1e-9


def test_padded_area_small():
    assert abs(geo.padded_area(4, 5) - 22.0) < 1e-9


def test_border_regression():
    assert abs(geo.border_area(2, 2) - 2.1 * 2.1) < 1e-9
''',
            "expect_targets": {"geo.py"},
        },
        {
            "instruction": "geo.py 新增 padded_perimeter(w, h)：按 2*(w+h)*(1 + MARGIN) 计算。MARGIN 口径与 units.py 一致。",
            "eval": '''\
import geo


def test_padded_perimeter():
    assert abs(geo.padded_perimeter(10, 20) - 66.0) < 1e-9


def test_padded_area_regression():
    assert abs(geo.padded_area(10, 10) - 110.0) < 1e-9
''',
            "expect_targets": {"geo.py"},
        },
    ],
    ref={
        1: {
            "geo.py": '''\
"""Geometry helpers."""
from units import MARGIN


def area(w, h):
    return w * h


def border_area(w, h):
    return (w + MARGIN) * (h + MARGIN)


def padded_area(w, h):
    return w * h * (1 + MARGIN)
''',
        },
        2: {
            "geo.py": '''\
"""Geometry helpers."""
from units import MARGIN


def area(w, h):
    return w * h


def border_area(w, h):
    return (w + MARGIN) * (h + MARGIN)


def padded_area(w, h):
    return w * h * (1 + MARGIN)


def padded_perimeter(w, h):
    return 2 * (w + h) * (1 + MARGIN)
''',
        },
    },
)

# ------------------------------------------------ D02 两层调用链（长）
T(
    id="v13_D02",
    type="two_hop_call_chain",
    difficulty="long",
    focus="闭包深度 d=2：converter→parserx→cleanup",
    files={
        "cleanup.py": '''\
"""Text cleanup helpers."""


def strip_noise(s):
    return "".join(ch for ch in s if ch.isprintable())


def squash(s):
    return " ".join(s.split())
''',
        "parserx.py": '''\
"""Parsing helpers."""
from cleanup import squash


def normalize(s):
    return squash(s)


def fields(line):
    return line.split(",")
''',
        "converter.py": '''\
"""Conversion entry points."""
from parserx import normalize


def convert(line):
    return normalize(line).upper()
''',
        "cli2.py": '''\
"""CLI helpers."""


def banner():
    return "converter-ready"


def run_argv(argv):
    return [banner()] + list(argv)
''',
    },
    steps=[
        {
            "instruction": "请修改 parserx.py 中的 normalize(s)：应去除首尾空白并转为小写（当前仅压缩空白）。",
            "eval": '''\
from parserx import normalize


def test_strip_and_lower():
    assert normalize("  Ab C  ") == "ab c"


def test_squeeze_still_works():
    assert normalize("a  b") == "a b"
''',
            "expect_targets": {"parserx.py"},
        },
        {
            "instruction": "converter.py 新增 bulk(lines)：对每行调用 convert 后以 `|` 拼接（空输入返回空串）。",
            "eval": '''\
from converter import convert, bulk
from parserx import normalize


def test_bulk():
    assert bulk(["x y", "z"]) == "X Y|Z"


def test_bulk_empty():
    assert bulk([]) == ""


def test_convert_regression():
    assert convert("  ab ") == "AB"


def test_normalize_regression():
    assert normalize("  Ab ") == "ab"
''',
            "expect_targets": {"converter.py"},
        },
    ],
    ref={
        1: {
            "parserx.py": '''\
"""Parsing helpers."""
from cleanup import squash


def normalize(s):
    return squash(s).lower()


def fields(line):
    return line.split(",")
''',
        },
        2: {
            "parserx.py": '''\
"""Parsing helpers."""
from cleanup import squash


def normalize(s):
    return squash(s).lower()


def fields(line):
    return line.split(",")
''',
            "converter.py": '''\
"""Conversion entry points."""
from parserx import normalize


def convert(line):
    return normalize(line).upper()


def bulk(lines):
    if not lines:
        return ""
    return "|".join(convert(ln) for ln in lines)
''',
        },
    },
)

# ------------------------------------------------ D03 依赖 + 边界值（长）
T(
    id="v13_D03",
    type="dep_and_boundary",
    difficulty="long",
    focus="依赖提供方 + 恰好值边界",
    files={
        "tiers.py": '''\
"""Fee tier policies."""

BASE_FEE = 4


def tier(amount):
    if amount > 200:
        return "gold"
    if amount > 50:
        return "silver"
    return "basic"
''',
        "charges.py": '''\
"""Charge computation."""
from tiers import tier


def apply_fee(amount, fee):
    return amount + fee


def describe(amount):
    return tier(amount)
''',
        "audit_log.py": '''\
"""Audit trail."""

EVENTS = []


def record(name):
    EVENTS.append(name)
    return len(EVENTS)


def last():
    return EVENTS[-1] if EVENTS else None
''',
    },
    steps=[
        {
            "instruction": "请修改 charges.py 中的 apply_fee，使其支持 fee 缺省为 None。None 时的计费基数记录在 tiers.py，按其取值执行。",
            "eval": '''\
import pytest
from charges import apply_fee
from tiers import BASE_FEE


def test_default_fee_uses_base():
    assert apply_fee(100) == 100 + BASE_FEE


def test_explicit_fee_unchanged():
    assert apply_fee(100, 5) == 105
''',
            "expect_targets": {"charges.py"},
        },
        {
            "instruction": "请修改 tiers.py 中的 tier(amount)：amount 恰为 200 时应归入 `gold`（当前仅大于 200 才算 gold）。",
            "eval": '''\
from charges import apply_fee, describe
from tiers import BASE_FEE, tier


def test_boundary_200_gold():
    assert tier(200) == "gold"


def test_just_below():
    assert tier(199.99) == "silver"


def test_default_fee_regression():
    assert apply_fee(10) == 10 + BASE_FEE


def test_describe_follows_tier():
    assert describe(200) == "gold"
''',
            "expect_targets": {"tiers.py"},
        },
    ],
    ref={
        1: {
            "charges.py": '''\
"""Charge computation."""
from tiers import tier, BASE_FEE


def apply_fee(amount, fee=None):
    if fee is None:
        fee = BASE_FEE
    return amount + fee


def describe(amount):
    return tier(amount)
''',
        },
        2: {
            "charges.py": '''\
"""Charge computation."""
from tiers import tier, BASE_FEE


def apply_fee(amount, fee=None):
    if fee is None:
        fee = BASE_FEE
    return amount + fee


def describe(amount):
    return tier(amount)
''',
            "tiers.py": '''\
"""Fee tier policies."""

BASE_FEE = 4


def tier(amount):
    if amount >= 200:
        return "gold"
    if amount > 50:
        return "silver"
    return "basic"
''',
        },
    },
)

# ------------------------------------------------ R01 数据结构 dict/list（中）
T(
    id="v13_R01",
    type="data_structure",
    difficulty="medium",
    focus="dict/list 结构：历史记录与保序聚合",
    files={
        "metrics_store.py": '''\
"""Metric point storage."""

DATA = {}
HISTORY = {}


def put(k, v):
    DATA[k] = v
    return DATA


def get(k):
    return DATA.get(k)
''',
        "reporting.py": '''\
"""Reporting helpers."""


def summarize(rows):
    out = {}
    for r in rows:
        out.setdefault(r["group"], set()).add(r["value"])
    return out


def groups(rows):
    return sorted({r["group"] for r in rows})
''',
    },
    steps=[
        {
            "instruction": "请修改 metrics_store.py 中的 put(k, v)：应同时在 HISTORY[k] 中按写入顺序记录每次的 v（当前 HISTORY 不更新）。",
            "eval": '''\
import metrics_store as ms


def test_history_appends_in_order():
    ms.put("seq_a", 1)
    ms.put("seq_a", 2)
    assert ms.HISTORY["seq_a"] == [1, 2]


def test_data_holds_latest():
    ms.put("latest_b", 9)
    assert ms.get("latest_b") == 9
''',
            "expect_targets": {"metrics_store.py"},
        },
        {
            "instruction": "reporting.py 中的 summarize(rows) 应返回 dict：每个 group 对应按输入顺序排列的 value 列表（当前用 set 去重丢顺序）。",
            "eval": '''\
import metrics_store as ms
from reporting import summarize


def test_order_and_duplicates_kept():
    rows = [
        {"group": "x", "value": 1},
        {"group": "x", "value": 2},
        {"group": "x", "value": 1},
        {"group": "y", "value": 5},
    ]
    assert summarize(rows) == {"x": [1, 2, 1], "y": [5]}


def test_store_regression():
    ms.put("reg_c", 3)
    assert ms.HISTORY["reg_c"] == [3]
''',
            "expect_targets": {"reporting.py"},
        },
    ],
    ref={
        1: {
            "metrics_store.py": '''\
"""Metric point storage."""

DATA = {}
HISTORY = {}


def put(k, v):
    DATA[k] = v
    HISTORY.setdefault(k, []).append(v)
    return DATA


def get(k):
    return DATA.get(k)
''',
        },
        2: {
            "metrics_store.py": '''\
"""Metric point storage."""

DATA = {}
HISTORY = {}


def put(k, v):
    DATA[k] = v
    HISTORY.setdefault(k, []).append(v)
    return DATA


def get(k):
    return DATA.get(k)
''',
            "reporting.py": '''\
"""Reporting helpers."""


def summarize(rows):
    out = {}
    for r in rows:
        out.setdefault(r["group"], []).append(r["value"])
    return out


def groups(rows):
    return sorted({r["group"] for r in rows})
''',
        },
    },
)

# ------------------------------------------------ R02 类型/契约约束（中）
T(
    id="v13_R02",
    type="contract_constraint",
    difficulty="medium",
    focus="接口契约：非法 factor 与契约传播",
    files={
        "shapes.py": '''\
"""Shape primitives."""

import math


class Circle:
    def __init__(self, r):
        self.r = r

    def area(self):
        return math.pi * self.r * self.r

    def scale(self, factor):
        self.r *= factor
        return self


class Rect:
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def area(self):
        return self.w * self.h

    def scale(self, factor):
        self.w *= factor
        self.h *= factor
        return self
''',
        "layout.py": '''\
"""Layout aggregation."""


def total_area(items):
    return sum(it.area() for it in items)


def place(item, dx, dy):
    return (dx, dy)
''',
    },
    steps=[
        {
            "instruction": "请修改 shapes.py 中的 Circle.scale(factor) 与 Rect.scale(factor)：factor ≤ 0 时应抛 ValueError（当前接受任意 factor）。",
            "eval": '''\
import math
import pytest
from shapes import Circle, Rect


def test_scale_ok():
    c = Circle(2)
    c.scale(3)
    assert abs(c.area() - math.pi * 36) < 1e-6


def test_invalid_zero_factor():
    with pytest.raises(ValueError):
        Circle(1).scale(0)


def test_invalid_negative_factor():
    with pytest.raises(ValueError):
        Rect(1, 1).scale(-1)
''',
            "expect_targets": {"shapes.py"},
        },
        {
            "instruction": "layout.py 新增 scaled_areas(items, factor)：对每个 item 调用 scale(factor) 并收集 area 列表；factor 非法时应整体抛 ValueError。",
            "eval": '''\
import math
import pytest
from layout import scaled_areas
from shapes import Circle, Rect


def test_scaled_areas():
    items = [Circle(1), Rect(2, 3)]
    out = scaled_areas(items, 2)
    assert len(out) == 2
    assert abs(out[0] - math.pi * 4) < 1e-6
    assert out[1] == 24


def test_invalid_factor_propagates():
    with pytest.raises(ValueError):
        scaled_areas([Circle(1)], 0)


def test_scale_contract_regression():
    with pytest.raises(ValueError):
        Circle(1).scale(-2)
''',
            "expect_targets": {"layout.py"},
        },
    ],
    ref={
        1: {
            "shapes.py": '''\
"""Shape primitives."""

import math


class Circle:
    def __init__(self, r):
        self.r = r

    def area(self):
        return math.pi * self.r * self.r

    def scale(self, factor):
        if factor <= 0:
            raise ValueError("factor must be > 0")
        self.r *= factor
        return self


class Rect:
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def area(self):
        return self.w * self.h

    def scale(self, factor):
        if factor <= 0:
            raise ValueError("factor must be > 0")
        self.w *= factor
        self.h *= factor
        return self
''',
        },
        2: {
            "shapes.py": '''\
"""Shape primitives."""

import math


class Circle:
    def __init__(self, r):
        self.r = r

    def area(self):
        return math.pi * self.r * self.r

    def scale(self, factor):
        if factor <= 0:
            raise ValueError("factor must be > 0")
        self.r *= factor
        return self


class Rect:
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def area(self):
        return self.w * self.h

    def scale(self, factor):
        if factor <= 0:
            raise ValueError("factor must be > 0")
        self.w *= factor
        self.h *= factor
        return self
''',
            "layout.py": '''\
"""Layout aggregation."""


def total_area(items):
    return sum(it.area() for it in items)


def place(item, dx, dy):
    return (dx, dy)


def scaled_areas(items, factor):
    out = []
    for it in items:
        it.scale(factor)
        out.append(it.area())
    return out
''',
        },
    },
)

# ------------------------------------------------ I01 相关文件含关键实现体（长）
T(
    id="v13_I01",
    type="impl_body_related",
    difficulty="long",
    focus="相关文件含关键实现体（与 CFD03 同型，全集仅此 1 个）",
    files={
        "engine.py": '''\
"""Quote engine."""


def quote(t):
    return t * 2


def adjust(q):
    return max(q, 0)
''',
        "curves_body.py": '''\
"""Calibration curves (implementation detail)."""


def calibrate(t):
    table = {0: 1, 1: 3, 2: 4, 3: 7, 4: 9, 5: 12, 6: 16, 7: 21, 8: 27, 9: 34}
    if t in table:
        return table[t]
    return 34 + (t - 9) * 7
''',
        "registry.py": '''\
"""Registry of engines."""

REGISTRY = {"default": "engine"}


def register(name):
    REGISTRY[name] = True
    return name
''',
    },
    steps=[
        {
            "instruction": "请修改 engine.py 中的 quote(t)。系数以 curves_body.py 中 calibrate 的系数表为准。实现须在 engine.py 内独立完成，不依赖外部模块导入。",
            "eval": '''\
import engine
from curves_body import calibrate


def test_matches_calibrate_table():
    for t in range(0, 13):
        assert engine.quote(t) == calibrate(t)


def test_adjust_regression():
    assert engine.adjust(-5) == 0
''',
            "expect_targets": {"engine.py"},
        },
        {
            "instruction": "engine.py 新增 quote_sum(ts)：对 ts 中每个 t 的 quote(t) 求和（空列表返回 0）。",
            "eval": '''\
import engine
from curves_body import calibrate


def test_quote_sum():
    assert engine.quote_sum([0, 1, 2]) == calibrate(0) + calibrate(1) + calibrate(2)


def test_quote_sum_empty():
    assert engine.quote_sum([]) == 0


def test_quote_regression():
    assert engine.quote(9) == calibrate(9)
''',
            "expect_targets": {"engine.py"},
        },
    ],
    ref={
        1: {
            "engine.py": '''\
"""Quote engine."""


def quote(t):
    table = {0: 1, 1: 3, 2: 4, 3: 7, 4: 9, 5: 12, 6: 16, 7: 21, 8: 27, 9: 34}
    if t in table:
        return table[t]
    return 34 + (t - 9) * 7


def adjust(q):
    return max(q, 0)
''',
        },
        2: {
            "engine.py": '''\
"""Quote engine."""


def quote(t):
    table = {0: 1, 1: 3, 2: 4, 3: 7, 4: 9, 5: 12, 6: 16, 7: 21, 8: 27, 9: 34}
    if t in table:
        return table[t]
    return 34 + (t - 9) * 7


def adjust(q):
    return max(q, 0)


def quote_sum(ts):
    return sum(quote(t) for t in ts)
''',
        },
    },
)

# ------------------------------------------------ I02 相关文件仅常量/辅助（短）
T(
    id="v13_I02",
    type="constants_only_related",
    difficulty="short",
    focus="相关文件仅常量（预期偏 Digest）",
    files={
        "pipeline.py": '''\
"""Processing pipeline."""


def run(item):
    return f"cat:{item}"


def run_all(items):
    return [run(i) for i in items]
''',
        "catalog_meta.py": '''\
"""Catalog metadata (constants only)."""

VERSION = "v2"
PREFIX = "cat"
''',
        "sinks.py": '''\
"""Output sinks."""


def join(items, sep=";"):
    return sep.join(items)


def emit(items):
    return join(items)
''',
    },
    steps=[
        {
            "instruction": "请修改 pipeline.py 中的 run(item)：输出标签应为 `v2`。标签口径与 catalog_meta.py 的版本设置一致。",
            "eval": '''\
import pipeline


def test_run_label():
    assert pipeline.run("x") == "v2:x"


def test_run_all_regression():
    assert pipeline.run_all(["a", "b"]) == ["v2:a", "v2:b"]
''',
            "expect_targets": {"pipeline.py"},
        },
        {
            "instruction": "请修改 sinks.py 中的 emit(items)：应先对每个 item 调用 pipeline.run 再以 `;` 拼接（当前直接拼接原样 item）。",
            "eval": '''\
import pipeline
from sinks import emit


def test_emit_through_pipeline():
    assert emit(["a", "b"]) == "v2:a;v2:b"


def test_run_regression():
    assert pipeline.run("z") == "v2:z"
''',
            "expect_targets": {"sinks.py", "pipeline.py"},
        },
    ],
    ref={
        1: {
            "pipeline.py": '''\
"""Processing pipeline."""


def run(item):
    return f"v2:{item}"


def run_all(items):
    return [run(i) for i in items]
''',
        },
        2: {
            "pipeline.py": '''\
"""Processing pipeline."""


def run(item):
    return f"v2:{item}"


def run_all(items):
    return [run(i) for i in items]
''',
            "sinks.py": '''\
"""Output sinks."""
from pipeline import run


def join(items, sep=";"):
    return sep.join(items)


def emit(items):
    return join([run(i) for i in items])
''',
        },
    },
)

# ------------------------------------------------ X01 多模块协作 3 文件（长）
T(
    id="v13_X01",
    type="cross_module_three_files",
    difficulty="long",
    focus="三模块协作：ingest ↔ verify ↔ warehouse",
    files={
        "verify.py": '''\
"""Row verification."""


def check(row):
    return row.get("qty", 0) > 0


def errors(rows):
    return [r for r in rows if not check(r)]
''',
        "ingest.py": '''\
"""Ingestion."""
from verify import check


def load(rows):
    return list(rows)


def keys(rows):
    return [r["id"] for r in rows]
''',
        "warehouse.py": '''\
"""Storage commitments."""

BIN = []


def store(rows):
    BIN.extend(rows)
    return len(BIN)
''',
    },
    steps=[
        {
            "instruction": "请修改 ingest.py 中的 load(rows)：丢弃未通过 verify.check 的行（当前全量返回）。",
            "eval": '''\
from ingest import load


def test_filters_invalid_rows():
    rows = [{"id": 1, "qty": 2}, {"id": 2, "qty": 0}, {"id": 3, "qty": -1}]
    assert load(rows) == [{"id": 1, "qty": 2}]


def test_empty_input():
    assert load([]) == []
''',
            "expect_targets": {"ingest.py", "verify.py"},
        },
        {
            "instruction": "warehouse.py 新增 commit(rows)：返回字典 {'kept': 过滤后行数, 'rejected': 被拒绝行数}，过滤口径与 ingest.load 一致。",
            "eval": '''\
from ingest import load
from warehouse import commit


def test_commit_counts():
    rows = [{"id": 1, "qty": 2}, {"id": 2, "qty": 0}]
    assert commit(rows) == {"kept": 1, "rejected": 1}


def test_commit_all_rejected():
    assert commit([{"qty": 0}]) == {"kept": 0, "rejected": 1}


def test_load_regression():
    rows = [{"id": 1, "qty": 2}, {"id": 2, "qty": 0}]
    assert load(rows) == [{"id": 1, "qty": 2}]
''',
            "expect_targets": {"warehouse.py", "ingest.py"},
        },
    ],
    ref={
        1: {
            "ingest.py": '''\
"""Ingestion."""
from verify import check


def load(rows):
    return [r for r in rows if check(r)]


def keys(rows):
    return [r["id"] for r in rows]
''',
        },
        2: {
            "ingest.py": '''\
"""Ingestion."""
from verify import check


def load(rows):
    return [r for r in rows if check(r)]


def keys(rows):
    return [r["id"] for r in rows]
''',
            "warehouse.py": '''\
"""Storage commitments."""

BIN = []


def store(rows):
    BIN.extend(rows)
    return len(BIN)


def commit(rows):
    kept = sum(1 for r in rows if r.get("qty", 0) > 0)
    return {"kept": kept, "rejected": len(rows) - kept}
''',
        },
    },
)

# ============================================================ 工具
import ast as _ast

sys.path.insert(0, str(P1 / "scripts"))
from p1_common import run_eval  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    return sha256_bytes(s.encode("utf-8"))


def write_text(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8", newline="\n")


def dir_fingerprints(d: Path) -> tuple[dict[str, str], str]:
    """目录内全部文件 → {相对路径: sha256} + 聚合 sha256。"""
    out: dict[str, str] = {}
    for p in sorted(d.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            rel = p.relative_to(d).as_posix()
            out[rel] = sha256_bytes(p.read_bytes())
    agg = sha256_text("\n".join(f"{k}:{v}" for k, v in sorted(out.items())))
    return out, agg


def symbol_map(files: dict[str, str]) -> dict[str, list[str]]:
    """顶层 FunctionDef/ClassDef 名 → 文件（AST 近似 store 的短名索引）。"""
    m: dict[str, list[str]] = {}
    for rel, src in files.items():
        try:
            tree = _ast.parse(src)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ( _ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
                m.setdefault(node.name, []).append(rel)
    return m


def materialize(task: dict, base: Path) -> None:
    tdir = base / task["id"]
    for rel, content in task["files"].items():
        write_text(tdir / "project" / rel, content)
    for i, step in enumerate(task["steps"], 1):
        write_text(tdir / "eval" / f"step{i}" / "test_behavior.py", step["eval"])
    # reference/stepN = 初始 project + 1..N 的覆盖（累计）
    for i in range(1, len(task["steps"]) + 1):
        acc = dict(task["files"])
        for k in range(1, i + 1):
            acc.update(task["ref"][k])
        for rel, content in acc.items():
            write_text(tdir / "reference" / f"step{i}" / rel, content)

# ============================================================ 主流程
def v1_instruction_set() -> set[str]:
    meta = json.loads((V1_TASKS / "tasks_v1.0.json").read_text(encoding="utf-8"))
    return {
        s["instruction"].strip()
        for e in meta["episodes"]
        for s in e["steps"]
    }


def v1_file_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(V1_TASKS.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            out[sha256_bytes(p.read_bytes())] = p.relative_to(V1_TASKS).as_posix()
    return out


def main() -> int:
    # 冻结文件核验
    rev3_now = sha256_bytes(REV3_PATH.read_bytes())
    if rev3_now != REV3_SHA256:
        print(f"REV3 SHA MISMATCH: {rev3_now}", file=sys.stderr)
        return 3
    if (HERE / "holdout_manifest.json").exists():
        print("holdout_manifest.json already exists (freeze-once). Refusing.", file=sys.stderr)
        return 2

    assert len(TASKS) == 12, f"expected 12 tasks, got {len(TASKS)}"
    ids = [t["id"] for t in TASKS]
    assert len(set(ids)) == 12

    # 类型配额（先于写任务固定，与原计划 §2.2 清单一致）
    quota = [
        ("v13_S01", "single_file_edit"), ("v13_S02", "single_file_boundary"),
        ("v13_M01", "multi_file_no_dep"), ("v13_M02", "weak_naming_ambiguity"),
        ("v13_D01", "explicit_import_dep"), ("v13_D02", "two_hop_call_chain"),
        ("v13_D03", "dep_and_boundary"), ("v13_R01", "data_structure"),
        ("v13_R02", "contract_constraint"), ("v13_I01", "impl_body_related"),
        ("v13_I02", "constants_only_related"), ("v13_X01", "cross_module_three_files"),
    ]
    for (qid, qtype), t in zip(quota, TASKS, strict=True):
        assert t["id"] == qid and t["type"] == qtype, (t["id"], qid, t["type"], qtype)
    diff = [t["difficulty"] for t in TASKS]
    assert diff.count("short") == 4 and diff.count("medium") == 4 and diff.count("long") == 4, diff

    # 生成
    for t in TASKS:
        materialize(t, HERE)

    # ---------- 验证 1：eval 初态失败 / 参考解通过
    validation = {"initial_fail": [], "ref_pass": [], "step2_discriminating": [], "targets_ok": []}
    for t in TASKS:
        tdir = HERE / t["id"]
        # step1: 初始必须失败
        ok, _ = run_eval(tdir / "project", tdir / "eval" / "step1", timeout=60)
        assert not ok, f"{t['id']} eval1 passes on initial project"
        validation["initial_fail"].append(t["id"] + "/step1")
        # step1: 参考解必须通过
        ok, out = run_eval(tdir / "reference" / "step1", tdir / "eval" / "step1", timeout=60)
        assert ok, f"{t['id']} eval1 fails on reference/step1:\n{out}"
        validation["ref_pass"].append(t["id"] + "/step1")
        # step2: 在 step1 参考解上必须失败（区分度）
        ok, _ = run_eval(tdir / "reference" / "step1", tdir / "eval" / "step2", timeout=60)
        assert not ok, f"{t['id']} eval2 already passes after step1 only"
        validation["step2_discriminating"].append(t["id"] + "/step2")
        # step2: 参考解必须通过
        ok, out = run_eval(tdir / "reference" / "step2", tdir / "eval" / "step2", timeout=60)
        assert ok, f"{t['id']} eval2 fails on reference/step2:\n{out}"
        validation["ref_pass"].append(t["id"] + "/step2")

        # ---------- 验证 2：edit target 解析
        files = sorted(t["files"])
        smap = symbol_map(t["files"])
        for i, step in enumerate(t["steps"], 1):
            res = parse_edit_targets(step["instruction"], files, smap)
            got = set(res.exact_paths)
            want = set(step["expect_targets"])
            assert got == want, f"{t['id']} step{i} targets {got} != expected {want}; reasons={res.reasons}"
            validation["targets_ok"].append(f"{t['id']}/step{i}")

    # ---------- 验证 3：与 v1 文件 hash 交集为空
    v1h = v1_file_hashes()
    holdout_h: dict[str, str] = {}
    for t in TASKS:
        for sub in ("project", "eval", "reference"):
            d = HERE / t["id"] / sub
            for p in sorted(d.rglob("*")):
                if p.is_file() and "__pycache__" not in p.parts:
                    holdout_h[sha256_bytes(p.read_bytes())] = p.relative_to(HERE).as_posix()
    overlap = sorted(set(v1h) & set(holdout_h))
    assert not overlap, f"hash overlap with v1: {[v1h[h] for h in overlap]}"

    # ---------- 验证 4：指令不逐字复用 v1
    v1ins = v1_instruction_set()
    overlaps = []
    for t in TASKS:
        for s in t["steps"]:
            mine = s["instruction"].strip()
            for other in v1ins:
                if mine == other or mine in other or other in mine:
                    overlaps.append((t["id"], mine, other))
    assert not overlaps, f"verbatim instruction overlap: {overlaps}"

    # ---------- holdout_tasks.json（冻结）
    frozen_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    episodes = []
    for t in TASKS:
        episodes.append(
            {
                "id": t["id"],
                "type": t["type"],
                "difficulty": t["difficulty"],
                "focus": t["focus"],
                "design_notes": ["rev3-holdout", "frozen-before-any-model-request"],
                "steps": [
                    {
                        "id": f"step{i}",
                        "instruction": s["instruction"],
                        "eval": f"eval/step{i}",
                        "expected_edit_targets": sorted(s["expect_targets"]),
                    }
                    for i, s in enumerate(t["steps"], 1)
                ],
            }
        )
    tasks_doc = {
        "task_set_version": "v1.3-holdout-m2-r1",
        "frozen_at": frozen_at,
        "source_design": "p1/experiments/v12_p1_execution/v13_design/v13_m2_validation_plan_rev3.md",
        "source_design_sha256": REV3_SHA256,
        "frozen_rules": {
            "arms": ["E", "F", "V13A"],
            "R": 2,
            "episodes": 72,
            "max_requests": 144,
            "randomization_seed": 20261103,
            "bootstrap_seed": 20261102,
            "bootstrap_B": 10000,
            "stat_cluster": "task_id",
            "no_task_edits_after_freeze": True,
        },
        "episodes": episodes,
    }
    write_text(HERE / "holdout_tasks.json", json.dumps(tasks_doc, ensure_ascii=False, indent=2) + "\n")
    tasks_sha = sha256_bytes((HERE / "holdout_tasks.json").read_bytes())

    # ---------- holdout_manifest.json（冻结）
    task_entries = []
    for t in TASKS:
        tdir = HERE / t["id"]
        proj_fp, proj_agg = dir_fingerprints(tdir / "project")
        eval_sha: dict[str, str] = {}
        ref_sha: dict[str, str] = {}
        step_entries = []
        for i, s in enumerate(t["steps"], 1):
            _, ev_agg = dir_fingerprints(tdir / "eval" / f"step{i}")
            _, rf_agg = dir_fingerprints(tdir / "reference" / f"step{i}")
            eval_sha[f"step{i}"] = ev_agg
            ref_sha[f"step{i}"] = rf_agg
            step_entries.append(
                {
                    "id": f"step{i}",
                    "instruction_sha256": sha256_text(s["instruction"]),
                    "eval_aggregate_sha256": ev_agg,
                    "expected_edit_targets": sorted(s["expect_targets"]),
                }
            )
        instr_agg = sha256_text("\n".join(s["instruction"] for s in t["steps"]))
        task_entries.append(
            {
                "id": t["id"],
                "type": t["type"],
                "difficulty": t["difficulty"],
                "focus": t["focus"],
                "instruction_sha256": instr_agg,
                "project_files_sha256": proj_fp,
                "project_aggregate_sha256": proj_agg,
                "eval_sha256": eval_sha,
                "reference_sha256": ref_sha,
                "steps": step_entries,
            }
        )

    manifest = {
        "schema": "v13-holdout-manifest-v1",
        "frozen_at": frozen_at,
        "freeze_policy": "created+validated then frozen; no edits after any model request",
        "plan": {
            "path": "p1/experiments/v12_p1_execution/v13_design/v13_m2_validation_plan_rev3.md",
            "sha256": REV3_SHA256,
        },
        "type_quota_frozen_before_writing": [
            {"id": qid, "type": qtype} for qid, qtype in quota
        ],
        "holdout_tasks_sha256": tasks_sha,
        "tasks": task_entries,
        "independence": {
            "v1_file_count": len(v1h),
            "holdout_file_count": len(holdout_h),
            "hash_intersection": [],
            "instruction_method": "normalized containment check vs tasks_v1.0.json instructions",
            "instruction_overlap": [],
        },
        "validation": validation,
        "generated_by": "p1/tasks_v13_holdout/make_holdout_v13.py",
    }
    write_text(HERE / "holdout_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    mf_sha = sha256_bytes((HERE / "holdout_manifest.json").read_bytes())

    print("HOLDOUT FROZEN")
    print(f"  tasks: {len(TASKS)}  steps_total: {sum(len(t['steps']) for t in TASKS)}")
    print(f"  difficulty: short={diff.count('short')} medium={diff.count('medium')} long={diff.count('long')}")
    print(f"  holdout_tasks.json sha256: {tasks_sha}")
    print(f"  holdout_manifest.json sha256: {mf_sha}")
    print(f"  v1 overlap: 0 / instruction overlap: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
