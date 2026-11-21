#!/usr/bin/env python
"""D1：剂量增补任务集 tasks_independent_v1_dose。

设计（对齐双 Token 补记 v2 的寻址友好要求）：
- 每步含正向「请参考 <file> …」相关非目标（非编辑目标）
- 5 步/题，跨轮复用常量/辅助模块
- 禁词 / 指令包含 / 文件 sha 交集 对 v1∪holdout∪P1∪independent = 0

输出：p1/tasks_independent_v1_dose/
  - 任务树 project/eval/reference
  - independent_dose_tasks.json
  - leakage_audit.json
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

P1 = Path(__file__).resolve().parents[1]  # p1/
OUT = P1 / "tasks_independent_v1_dose"
FORBIDDEN = [
    "memory", "上下文", "记忆", "复用", "reuse", "context window",
    "REUSE_KV", "symbol_full", "memory_off", "V12", "V12F", "v12",
]


def write_tree(base: Path, files: dict[str, str]) -> None:
    if base.exists():
        shutil.rmtree(base)
    for rel, body in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def _pack(tid: str, project: dict, steps: list, refs: dict, evals: dict) -> dict:
    return {"id": tid, "steps": steps, "_project": project, "_refs": refs, "_evals": evals}


def tasks() -> list[dict]:
    out = []

    # D01: 计费常量 + 主逻辑（正向参考 consts）
    out.append(_pack(
        "dose_D01",
        {
            "bill_core.py": (
                "from fee_consts import BASE\n\n\n"
                "def charge(n):\n    return n\n"
            ),
            "fee_consts.py": (
                "BASE = 5\n"
                "LABEL = 'doseD01'\n\n\n"
                "def base():\n    return BASE\n\n\n"
                "def tag():\n    return LABEL\n"
            ),
            "ledger_noise.py": "def ledger_tick():\n    return 0\n",
        },
        [
            {"id": "step1", "instruction": "请参考 fee_consts.py 中的 BASE 定义。修改 bill_core.py 中的 charge(n)：返回 n + BASE。不要修改 fee_consts.py。", "eval": "eval/step1"},
            {"id": "step2", "instruction": "请参考 fee_consts.py 中的 LABEL。修改 bill_core.py 中的 charge(n)：返回 n + BASE * 2。不要修改 fee_consts.py。", "eval": "eval/step2"},
            {"id": "step3", "instruction": "请在 bill_core.py 新增 discount(n) 返回 charge(n) - 1。不要修改 fee_consts.py 与 ledger_noise.py。", "eval": "eval/step3"},
            {"id": "step4", "instruction": "请参考 fee_consts.py 的 BASE。修改 bill_core.py 中的 discount(n)：返回 charge(n) - BASE。不要修改 fee_consts.py。", "eval": "eval/step4"},
            {"id": "step5", "instruction": "请修改 bill_core.py 中的 charge(n)：当 n < 0 返回 0，否则 n + BASE * 2。不要修改 fee_consts.py。", "eval": "eval/step5"},
        ],
        {
            "step1": {"bill_core.py": "from fee_consts import BASE\n\n\ndef charge(n):\n    return n + BASE\n"},
            "step2": {"bill_core.py": "from fee_consts import BASE\n\n\ndef charge(n):\n    return n + BASE * 2\n"},
            "step3": {
                "bill_core.py": (
                    "from fee_consts import BASE\n\n\n"
                    "def charge(n):\n    return n + BASE * 2\n\n\n"
                    "def discount(n):\n    return charge(n) - 1\n"
                )
            },
            "step4": {
                "bill_core.py": (
                    "from fee_consts import BASE\n\n\n"
                    "def charge(n):\n    return n + BASE * 2\n\n\n"
                    "def discount(n):\n    return charge(n) - BASE\n"
                )
            },
            "step5": {
                "bill_core.py": (
                    "from fee_consts import BASE\n\n\n"
                    "def charge(n):\n    if n < 0:\n        return 0\n    return n + BASE * 2\n\n\n"
                    "def discount(n):\n    return charge(n) - BASE\n"
                )
            },
        },
        {
            "step1": "def test_t():\n    from bill_core import charge\n    assert charge(2) == 7\n",
            "step2": "def test_t():\n    from bill_core import charge\n    assert charge(2) == 12\n",
            "step3": "def test_t():\n    from bill_core import discount\n    assert discount(2) == 11\n",
            "step4": "def test_t():\n    from bill_core import discount\n    assert discount(2) == 7\n",
            "step5": "def test_t():\n    from bill_core import charge\n    assert charge(-1) == 0\n    assert charge(2) == 12\n",
        },
    ))

    # D02: 路由表 + handler
    out.append(_pack(
        "dose_D02",
        {
            "router.py": (
                "from route_table import DEFAULT_PATH\n\n\n"
                "def resolve(key):\n    return None\n"
            ),
            "route_table.py": (
                "DEFAULT_PATH = '/home'\n"
                "ALIAS = {'h': '/alias_home'}\n\n\n"
                "def default():\n    return DEFAULT_PATH\n\n\n"
                "def lookup(k):\n    return ALIAS.get(k)\n"
            ),
            "unused_trace.py": "def trace_noop():\n    return None\n",
        },
        [
            {"id": "step1", "instruction": "请参考 route_table.py 中的 DEFAULT_PATH。修改 router.py 中的 resolve(key)：未知键返回 DEFAULT_PATH。不要修改 route_table.py。", "eval": "eval/step1"},
            {"id": "step2", "instruction": "请参考 route_table.py 中的 ALIAS。修改 router.py 中的 resolve(key)：先查 ALIAS，未命中返回 DEFAULT_PATH。不要修改 route_table.py。", "eval": "eval/step2"},
            {"id": "step3", "instruction": "请在 router.py 新增 has_alias(key) 返回 key 是否在 ALIAS。不要修改 route_table.py 与 unused_trace.py。", "eval": "eval/step3"},
            {"id": "step4", "instruction": "请参考 route_table.py 的 DEFAULT_PATH。修改 router.py 中的 resolve(key)：未知键返回 None（不再回退 DEFAULT_PATH）。不要修改 route_table.py。", "eval": "eval/step4"},
            {"id": "step5", "instruction": "请修改 router.py 中的 has_alias(key)：单字符键不视为别名（长度至少 2）。不要修改 route_table.py。", "eval": "eval/step5"},
        ],
        {
            "step1": {"router.py": "from route_table import DEFAULT_PATH\n\n\ndef resolve(key):\n    if key is None:\n        return DEFAULT_PATH\n    return DEFAULT_PATH\n"},
            "step2": {
                "router.py": (
                    "from route_table import ALIAS, DEFAULT_PATH\n\n\n"
                    "def resolve(key):\n    if key in ALIAS:\n        return ALIAS[key]\n    return DEFAULT_PATH\n"
                )
            },
            "step3": {
                "router.py": (
                    "from route_table import ALIAS, DEFAULT_PATH\n\n\n"
                    "def resolve(key):\n    if key in ALIAS:\n        return ALIAS[key]\n    return DEFAULT_PATH\n\n\n"
                    "def has_alias(key):\n    return key in ALIAS\n"
                )
            },
            "step4": {
                "router.py": (
                    "from route_table import ALIAS, DEFAULT_PATH\n\n\n"
                    "def resolve(key):\n    if key in ALIAS:\n        return ALIAS[key]\n    return None\n\n\n"
                    "def has_alias(key):\n    return key in ALIAS\n"
                )
            },
            "step5": {
                "router.py": (
                    "from route_table import ALIAS, DEFAULT_PATH\n\n\n"
                    "def resolve(key):\n    if key in ALIAS:\n        return ALIAS[key]\n    return None\n\n\n"
                    "def has_alias(key):\n    if not isinstance(key, str) or len(key) < 2:\n        return False\n    return key in ALIAS\n"
                )
            },
        },
        {
            "step1": "def test_t():\n    from router import resolve\n    assert resolve('x') == '/home'\n",
            "step2": "def test_t():\n    from router import resolve\n    assert resolve('h') == '/alias_home'\n    assert resolve('z') == '/home'\n",
            "step3": "def test_t():\n    from router import has_alias\n    assert has_alias('h') is True\n    assert has_alias('z') is False\n",
            "step4": "def test_t():\n    from router import resolve\n    assert resolve('z') is None\n    assert resolve('h') == '/alias_home'\n",
            "step5": "def test_t():\n    from router import has_alias\n    assert has_alias('h') is False\n    assert has_alias('') is False\n",
        },
    ))

    # D03: 阈值 + filter
    out.append(_pack(
        "dose_D03",
        {
            "filter_core.py": (
                "from thresholds import CUT\n\n\n"
                "def keep(x):\n    return True\n"
            ),
            "thresholds.py": (
                "CUT = 10\n"
                "MAX_N = 20\n\n\n"
                "def cut():\n    return CUT\n\n\n"
                "def max_n():\n    return MAX_N\n"
            ),
            "bench_extra.py": "def bench_tick():\n    return 1\n",
        },
        [
            {"id": "step1", "instruction": "请参考 thresholds.py 中的 CUT。修改 filter_core.py 中的 keep(x)：返回 x >= CUT。不要修改 thresholds.py。", "eval": "eval/step1"},
            {"id": "step2", "instruction": "请参考 thresholds.py 中的 MAX_N。修改 filter_core.py 中的 keep(x)：返回 x >= CUT 且 x <= MAX_N。不要修改 thresholds.py。", "eval": "eval/step2"},
            {"id": "step3", "instruction": "请在 filter_core.py 新增 count(xs) 返回 keep 为真的个数。不要修改 thresholds.py 与 bench_extra.py。", "eval": "eval/step3"},
            {"id": "step4", "instruction": "请参考 thresholds.py 的 CUT。修改 filter_core.py 中的 keep(x)：只保留 x >= CUT（去掉 MAX_N 上限）。不要修改 thresholds.py。", "eval": "eval/step4"},
            {"id": "step5", "instruction": "请修改 filter_core.py 中的 keep(x)：改为严格大于 CUT（x > CUT）。不要修改 thresholds.py。", "eval": "eval/step5"},
        ],
        {
            "step1": {"filter_core.py": "from thresholds import CUT\n\n\ndef keep(x):\n    return x >= CUT\n"},
            "step2": {
                "filter_core.py": (
                    "from thresholds import CUT, MAX_N\n\n\n"
                    "def keep(x):\n    return x >= CUT and x <= MAX_N\n"
                )
            },
            "step3": {
                "filter_core.py": (
                    "from thresholds import CUT, MAX_N\n\n\n"
                    "def keep(x):\n    return x >= CUT and x <= MAX_N\n\n\n"
                    "def count(xs):\n    return sum(1 for x in xs if keep(x))\n"
                )
            },
            "step4": {
                "filter_core.py": (
                    "from thresholds import CUT\n\n\n"
                    "def keep(x):\n    return x >= CUT\n\n\n"
                    "def count(xs):\n    return sum(1 for x in xs if keep(x))\n"
                )
            },
            "step5": {
                "filter_core.py": (
                    "from thresholds import CUT\n\n\n"
                    "def keep(x):\n    return x > CUT\n\n\n"
                    "def count(xs):\n    if not xs:\n        return 0\n    return sum(1 for x in xs if keep(x))\n"
                )
            },
        },
        {
            "step1": "def test_t():\n    from filter_core import keep\n    assert keep(10) is True\n    assert keep(9) is False\n",
            "step2": "def test_t():\n    from filter_core import keep\n    assert keep(15) is True\n    assert keep(25) is False\n",
            "step3": "def test_t():\n    from filter_core import count\n    assert count([10, 11, 9]) == 2\n",
            "step4": "def test_t():\n    from filter_core import keep\n    assert keep(25) is True\n",
            "step5": "def test_t():\n    from filter_core import keep\n    assert keep(10) is False\n    assert keep(11) is True\n",
        },
    ))

    # D04: 文案常量 + formatter
    out.append(_pack(
        "dose_D04",
        {
            "fmt_core.py": (
                "from fmt_strings import SEP\n\n\n"
                "def join3(a, b, c):\n    return a + b + c\n"
            ),
            "fmt_strings.py": (
                "SEP = '-'\n"
                "EMPTY = ''\n\n\n"
                "def sep():\n    return SEP\n\n\n"
                "def empty():\n    return EMPTY\n"
            ),
            "scratch_pad.py": "def pad_mark():\n    return '#'\n",
        },
        [
            {"id": "step1", "instruction": "请参考 fmt_strings.py 中的 SEP。修改 fmt_core.py 中的 join3(a,b,c)：用 SEP 连接三者。不要修改 fmt_strings.py。", "eval": "eval/step1"},
            {"id": "step2", "instruction": "请参考 fmt_strings.py 中的 EMPTY。修改 fmt_core.py 中的 join3：任一参数为 None 时该位置用 EMPTY。不要修改 fmt_strings.py。", "eval": "eval/step2"},
            {"id": "step3", "instruction": "请在 fmt_core.py 新增 join_list(xs) 用 SEP 连接全部元素。不要修改 fmt_strings.py 与 scratch_pad.py。", "eval": "eval/step3"},
            {"id": "step4", "instruction": "请参考 fmt_strings.py 的 SEP。修改 fmt_core.py 中的 join_list：跳过 None 元素。不要修改 fmt_strings.py。", "eval": "eval/step4"},
            {"id": "step5", "instruction": "请修改 fmt_core.py 中的 join_list：返回 (文本, 有效元素个数) 元组。不要修改 fmt_strings.py。", "eval": "eval/step5"},
        ],
        {
            "step1": {
                "fmt_core.py": (
                    "from fmt_strings import SEP\n\n\n"
                    "def join3(a, b, c):\n    return a + SEP + b + SEP + c\n"
                )
            },
            "step2": {
                "fmt_core.py": (
                    "from fmt_strings import EMPTY, SEP\n\n\n"
                    "def join3(a, b, c):\n    parts = [EMPTY if x is None else x for x in (a, b, c)]\n    return parts[0] + SEP + parts[1] + SEP + parts[2]\n"
                )
            },
            "step3": {
                "fmt_core.py": (
                    "from fmt_strings import EMPTY, SEP\n\n\n"
                    "def join3(a, b, c):\n    parts = [EMPTY if x is None else x for x in (a, b, c)]\n    return parts[0] + SEP + parts[1] + SEP + parts[2]\n\n\n"
                    "def join_list(xs):\n    return SEP.join(xs)\n"
                )
            },
            "step4": {
                "fmt_core.py": (
                    "from fmt_strings import EMPTY, SEP\n\n\n"
                    "def join3(a, b, c):\n    parts = [EMPTY if x is None else x for x in (a, b, c)]\n    return parts[0] + SEP + parts[1] + SEP + parts[2]\n\n\n"
                    "def join_list(xs):\n    items = [x for x in xs if x is not None]\n    if not items:\n        return EMPTY\n    return SEP.join(items)\n"
                )
            },
            "step5": {
                "fmt_core.py": (
                    "from fmt_strings import EMPTY, SEP\n\n\n"
                    "def join3(a, b, c):\n    parts = [EMPTY if x is None else x for x in (a, b, c)]\n    return SEP.join(parts)\n\n\n"
                    "def join_list(xs):\n    items = [x for x in xs if x is not None]\n    if not items:\n        return (EMPTY, 0)\n    return (SEP.join(items), len(items))\n"
                )
            },
        },
        {
            "step1": "def test_t():\n    from fmt_core import join3\n    assert join3('a', 'b', 'c') == 'a-b-c'\n",
            "step2": "def test_t():\n    from fmt_core import join3\n    assert join3('a', None, 'c') == 'a--c'\n",
            "step3": "def test_t():\n    from fmt_core import join_list\n    assert join_list(['x', 'y']) == 'x-y'\n",
            "step4": "def test_t():\n    from fmt_core import join_list\n    assert join_list([None, 'a', None, 'b']) == 'a-b'\n",
            "step5": "def test_t():\n    from fmt_core import join_list\n    assert join_list([None, 'a', 'b']) == ('a-b', 2)\n",
        },
    ))

    # D05: 容量 + pool
    out.append(_pack(
        "dose_D05",
        {
            "pool_mgr.py": (
                "from pool_cap import CAP\n\n\n"
                "def acquire():\n    return 0\n"
            ),
            "pool_cap.py": (
                "CAP = 4\n"
                "NAME = 'doseD05'\n\n\n"
                "def cap():\n    return CAP\n\n\n"
                "def name():\n    return NAME\n"
            ),
            "pool_log.py": "def log_skip():\n    return None\n",
        },
        [
            {"id": "step1", "instruction": "请参考 pool_cap.py 中的 CAP。修改 pool_mgr.py 中的 acquire()：返回 CAP。不要修改 pool_cap.py。", "eval": "eval/step1"},
            {"id": "step2", "instruction": "请参考 pool_cap.py 的 CAP。修改 pool_mgr.py 中的 acquire()：返回 CAP - 1。不要修改 pool_cap.py。", "eval": "eval/step2"},
            {"id": "step3", "instruction": "请在 pool_mgr.py 新增 remaining(used) 返回 CAP - used。不要修改 pool_cap.py 与 pool_log.py。", "eval": "eval/step3"},
            {"id": "step4", "instruction": "请参考 pool_cap.py 的 CAP。修改 pool_mgr.py 中的 remaining(used)：used < 0 时返回 CAP。不要修改 pool_cap.py。", "eval": "eval/step4"},
            {"id": "step5", "instruction": "请修改 pool_mgr.py 中的 remaining(used)：used > CAP 时返回 0。不要修改 pool_cap.py。", "eval": "eval/step5"},
        ],
        {
            "step1": {"pool_mgr.py": "from pool_cap import CAP\n\n\ndef acquire():\n    return CAP\n"},
            "step2": {"pool_mgr.py": "from pool_cap import CAP\n\n\ndef acquire():\n    return CAP - 1\n"},
            "step3": {
                "pool_mgr.py": (
                    "from pool_cap import CAP\n\n\n"
                    "def acquire():\n    return CAP - 1\n\n\n"
                    "def remaining(used):\n    return CAP - used\n"
                )
            },
            "step4": {
                "pool_mgr.py": (
                    "from pool_cap import CAP\n\n\n"
                    "def acquire():\n    return CAP - 1\n\n\n"
                    "def remaining(used):\n    if used < 0:\n        return CAP\n    return CAP - used\n"
                )
            },
            "step5": {
                "pool_mgr.py": (
                    "from pool_cap import CAP\n\n\n"
                    "def acquire():\n    return CAP - 1\n\n\n"
                    "def remaining(used):\n    if used < 0:\n        return CAP\n    if used > CAP:\n        return 0\n    return CAP - used\n"
                )
            },
        },
        {
            "step1": "def test_t():\n    from pool_mgr import acquire\n    assert acquire() == 4\n",
            "step2": "def test_t():\n    from pool_mgr import acquire\n    assert acquire() == 3\n",
            "step3": "def test_t():\n    from pool_mgr import remaining\n    assert remaining(1) == 3\n",
            "step4": "def test_t():\n    from pool_mgr import remaining\n    assert remaining(-1) == 4\n",
            "step5": "def test_t():\n    from pool_mgr import remaining\n    assert remaining(99) == 0\n    assert remaining(1) == 3\n",
        },
    ))

    # D06: 模式串 + matcher
    out.append(_pack(
        "dose_D06",
        {
            "match_core.py": (
                "from match_pat import PREFIX\n\n\n"
                "def match(s):\n    return False\n"
            ),
            "match_pat.py": (
                "PREFIX = 'id_'\n"
                "SUFFIX = '_end'\n\n\n"
                "def prefix():\n    return PREFIX\n\n\n"
                "def suffix():\n    return SUFFIX\n"
            ),
            "match_noise.py": "def noise_ping():\n    return 'pong'\n",
        },
        [
            {"id": "step1", "instruction": "请参考 match_pat.py 中的 PREFIX。修改 match_core.py 中的 match(s)：返回 s 是否以 PREFIX 开头。不要修改 match_pat.py。", "eval": "eval/step1"},
            {"id": "step2", "instruction": "请参考 match_pat.py 中的 SUFFIX。修改 match_core.py 中的 match(s)：以 PREFIX 开头且以 SUFFIX 结尾。不要修改 match_pat.py。", "eval": "eval/step2"},
            {"id": "step3", "instruction": "请在 match_core.py 新增 strip_affix(s) 去掉首尾前后缀。不要修改 match_pat.py 与 match_noise.py。", "eval": "eval/step3"},
            {"id": "step4", "instruction": "请参考 match_pat.py 的 PREFIX。修改 match_core.py 中的 match(s)：s 为 None 返回 False。不要修改 match_pat.py。", "eval": "eval/step4"},
            {"id": "step5", "instruction": "请修改 match_core.py 中的 strip_affix(s)：非字符串输入原样返回。不要修改 match_pat.py。", "eval": "eval/step5"},
        ],
        {
            "step1": {
                "match_core.py": (
                    "from match_pat import PREFIX\n\n\n"
                    "def match(s):\n    return s.startswith(PREFIX)\n"
                )
            },
            "step2": {
                "match_core.py": (
                    "from match_pat import PREFIX, SUFFIX\n\n\n"
                    "def match(s):\n    return s.startswith(PREFIX) and s.endswith(SUFFIX)\n"
                )
            },
            "step3": {
                "match_core.py": (
                    "from match_pat import PREFIX, SUFFIX\n\n\n"
                    "def match(s):\n    return s.startswith(PREFIX) and s.endswith(SUFFIX)\n\n\n"
                    "def strip_affix(s):\n    body = s\n    if body.startswith(PREFIX):\n        body = body[len(PREFIX):]\n    if body.endswith(SUFFIX):\n        body = body[: -len(SUFFIX)]\n    return body\n"
                )
            },
            "step4": {
                "match_core.py": (
                    "from match_pat import PREFIX, SUFFIX\n\n\n"
                    "def match(s):\n    if s is None or s == '':\n        return False\n    return s.startswith(PREFIX) and s.endswith(SUFFIX)\n\n\n"
                    "def strip_affix(s):\n    body = s\n    if body.startswith(PREFIX):\n        body = body[len(PREFIX):]\n    if body.endswith(SUFFIX):\n        body = body[: -len(SUFFIX)]\n    return body\n"
                )
            },
            "step5": {
                "match_core.py": (
                    "from match_pat import PREFIX, SUFFIX\n\n\n"
                    "def match(s):\n    if s is None or s == '':\n        return False\n    return s.startswith(PREFIX) and s.endswith(SUFFIX)\n\n\n"
                    "def strip_affix(s):\n    if not isinstance(s, str):\n        return s\n    if not match(s):\n        return s\n    body = s[len(PREFIX):]\n    return body[: -len(SUFFIX)]\n"
                )
            },
        },
        {
            "step1": "def test_t():\n    from match_core import match\n    assert match('id_a') is True\n    assert match('xx') is False\n",
            "step2": "def test_t():\n    from match_core import match\n    assert match('id_a_end') is True\n    assert match('id_a') is False\n",
            "step3": "def test_t():\n    from match_core import strip_affix\n    assert strip_affix('id_a_end') == 'a'\n",
            "step4": "def test_t():\n    from match_core import match\n    assert match(None) is False\n",
            "step5": "def test_t():\n    from match_core import strip_affix\n    assert strip_affix(123) == 123\n",
        },
    ))

    # D07: 权重 + score
    out.append(_pack(
        "dose_D07",
        {
            "score_core.py": (
                "from score_w import W_BASE\n\n\n"
                "def score(v):\n    return v\n"
            ),
            "score_w.py": (
                "W_BASE = 2\n"
                "W_BONUS = 5\n\n\n"
                "def base():\n    return W_BASE\n\n\n"
                "def bonus():\n    return W_BONUS\n"
            ),
            "score_dump.py": "def dump_row():\n    return []\n",
        },
        [
            {"id": "step1", "instruction": "请参考 score_w.py 中的 W_BASE。修改 score_core.py 中的 score(v)：返回 v * W_BASE。不要修改 score_w.py。", "eval": "eval/step1"},
            {"id": "step2", "instruction": "请参考 score_w.py 中的 W_BONUS。修改 score_core.py 中的 score(v)：v > 0 时再加 W_BONUS。不要修改 score_w.py。", "eval": "eval/step2"},
            {"id": "step3", "instruction": "请在 score_core.py 新增 total(xs) 返回 score 之和。不要修改 score_w.py 与 score_dump.py。", "eval": "eval/step3"},
            {"id": "step4", "instruction": "请参考 score_w.py 的 W_BASE。修改 score_core.py 中的 score(v)：v < 0 返回 0。不要修改 score_w.py。", "eval": "eval/step4"},
            {"id": "step5", "instruction": "请修改 score_core.py 中的 total(xs)：返回最大 score 而非求和。不要修改 score_w.py。", "eval": "eval/step5"},
        ],
        {
            "step1": {"score_core.py": "from score_w import W_BASE\n\n\ndef score(v):\n    return v * W_BASE\n"},
            "step2": {
                "score_core.py": (
                    "from score_w import W_BASE, W_BONUS\n\n\n"
                    "def score(v):\n    s = v * W_BASE\n    if v > 0:\n        s += W_BONUS\n    return s\n"
                )
            },
            "step3": {
                "score_core.py": (
                    "from score_w import W_BASE, W_BONUS\n\n\n"
                    "def score(v):\n    s = v * W_BASE\n    if v > 0:\n        s += W_BONUS\n    return s\n\n\n"
                    "def total(xs):\n    return sum(score(v) for v in xs)\n"
                )
            },
            "step4": {
                "score_core.py": (
                    "from score_w import W_BASE, W_BONUS\n\n\n"
                    "def score(v):\n    if v < 0:\n        return 0\n    s = v * W_BASE\n    if v > 0:\n        s += W_BONUS\n    return s\n\n\n"
                    "def total(xs):\n    return sum(score(v) for v in xs)\n"
                )
            },
            "step5": {
                "score_core.py": (
                    "from score_w import W_BASE, W_BONUS\n\n\n"
                    "def score(v):\n    if v < 0:\n        return 0\n    s = v * W_BASE\n    if v > 0:\n        s += W_BONUS\n    return s\n\n\n"
                    "def total(xs):\n    if not xs:\n        return 0\n    return max(score(v) for v in xs)\n"
                )
            },
        },
        {
            "step1": "def test_t():\n    from score_core import score\n    assert score(3) == 6\n",
            "step2": "def test_t():\n    from score_core import score\n    assert score(3) == 11\n    assert score(0) == 0\n",
            "step3": "def test_t():\n    from score_core import total\n    assert total([1, 2]) == 16\n",
            "step4": "def test_t():\n    from score_core import score\n    assert score(-2) == 0\n",
            "step5": "def test_t():\n    from score_core import total\n    assert total([1, 2]) == 9\n    assert total([]) == 0\n",
        },
    ))

    # D08: 单位换算 + api
    out.append(_pack(
        "dose_D08",
        {
            "unit_api.py": (
                "from unit_scale import SCALE\n\n\n"
                "def to_display(x):\n    return x\n"
            ),
            "unit_scale.py": (
                "SCALE = 100\n"
                "UNIT = 'cents'\n\n\n"
                "def scale():\n    return SCALE\n\n\n"
                "def unit():\n    return UNIT\n"
            ),
            "unit_doc.py": "def doc_title():\n    return 'units'\n",
        },
        [
            {"id": "step1", "instruction": "请参考 unit_scale.py 中的 SCALE。修改 unit_api.py 中的 to_display(x)：返回 x * SCALE。不要修改 unit_scale.py。", "eval": "eval/step1"},
            {"id": "step2", "instruction": "请参考 unit_scale.py 中的 UNIT。修改 unit_api.py 中的 to_display(x)：返回元组 (x * SCALE, UNIT)。不要修改 unit_scale.py。", "eval": "eval/step2"},
            {"id": "step3", "instruction": "请在 unit_api.py 新增 from_display(y) 返回 y // SCALE。不要修改 unit_scale.py 与 unit_doc.py。", "eval": "eval/step3"},
            {"id": "step4", "instruction": "请参考 unit_scale.py 的 SCALE。修改 unit_api.py 中的 from_display(y)：y < 0 返回 0。不要修改 unit_scale.py。", "eval": "eval/step4"},
            {"id": "step5", "instruction": "请修改 unit_api.py 中的 to_display(x)：x < 0 返回 0。不要修改 unit_scale.py。", "eval": "eval/step5"},
        ],
        {
            "step1": {"unit_api.py": "from unit_scale import SCALE\n\n\ndef to_display(x):\n    return x * SCALE\n"},
            "step2": {
                "unit_api.py": (
                    "from unit_scale import SCALE, UNIT\n\n\n"
                    "def to_display(x):\n    return (x * SCALE, UNIT)\n"
                )
            },
            "step3": {
                "unit_api.py": (
                    "from unit_scale import SCALE, UNIT\n\n\n"
                    "def to_display(x):\n    return (x * SCALE, UNIT)\n\n\n"
                    "def from_display(y):\n    return y // SCALE\n"
                )
            },
            "step4": {
                "unit_api.py": (
                    "from unit_scale import SCALE, UNIT\n\n\n"
                    "def to_display(x):\n    return (x * SCALE, UNIT)\n\n\n"
                    "def from_display(y):\n    if y < 0:\n        return 0\n    return y // SCALE\n"
                )
            },
            "step5": {
                "unit_api.py": (
                    "from unit_scale import SCALE, UNIT\n\n\n"
                    "def to_display(x):\n    if x < 0:\n        return 0\n    return (x * SCALE, UNIT)\n\n\n"
                    "def from_display(y):\n    if y < 0:\n        return 0\n    return y // SCALE\n"
                )
            },
        },
        {
            "step1": "def test_t():\n    from unit_api import to_display\n    assert to_display(3) == 300\n",
            "step2": "def test_t():\n    from unit_api import to_display\n    assert to_display(3) == (300, 'cents')\n",
            "step3": "def test_t():\n    from unit_api import from_display\n    assert from_display(300) == 3\n",
            "step4": "def test_t():\n    from unit_api import from_display\n    assert from_display(-5) == 0\n",
            "step5": "def test_t():\n    from unit_api import to_display\n    assert to_display(-1) == 0\n",
        },
    ))

    return out


def materialize() -> dict:
    eps = tasks()
    if OUT.exists():
        for c in list(OUT.iterdir()):
            if c.name in ("make_dose_tasks.py",):
                continue
            if c.is_dir():
                shutil.rmtree(c)
            else:
                c.unlink()
    OUT.mkdir(parents=True, exist_ok=True)

    episodes = []
    for ep in eps:
        tid = ep["id"]
        write_tree(OUT / tid / "project", ep["_project"])
        state = dict(ep["_project"])
        for step in ep["steps"]:
            sid = step["id"]
            state = dict(state)
            state.update(ep["_refs"][sid])
            write_tree(OUT / tid / "reference" / sid, state)
            ev = OUT / tid / "eval" / sid
            ev.mkdir(parents=True, exist_ok=True)
            (ev / "test_behavior.py").write_text(ep["_evals"][sid], encoding="utf-8")
        episodes.append({"id": tid, "steps": ep["steps"]})

    # 判别性
    problems = []

    def run_eval(tree: Path, ev: Path) -> int:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            for f in tree.rglob("*.py"):
                dest = tdp / f.relative_to(tree)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(f.read_bytes())
            shutil.copy(ev, tdp / "test_behavior.py")
            r = subprocess.run(
                [sys.executable, "-m", "pytest", str(tdp / "test_behavior.py"), "-q"],
                capture_output=True,
                text=True,
            )
            return r.returncode

    for ep in eps:
        tid = ep["id"]
        steps = ep["steps"]
        for i, step in enumerate(steps):
            sid = step["id"]
            ev = OUT / tid / "eval" / sid / "test_behavior.py"
            ref = OUT / tid / "reference" / sid
            if run_eval(ref, ev) != 0:
                problems.append(f"{tid}/{sid} ref FAIL")
            prev = OUT / tid / "reference" / steps[i - 1]["id"] if i > 0 else OUT / tid / "project"
            if run_eval(prev, ev) == 0:
                problems.append(f"{tid}/{sid} prev PASS want FAIL")

    payload = {"schema": "independent-dose-tasks-v1", "episodes": episodes,
               "discrimination_problems": problems}
    (OUT / "independent_dose_tasks.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"episodes": episodes, "problems": problems}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def leakage_audit(episodes: list[dict]) -> dict:
    """禁词 + 指令包含 + 文件 sha 交集（对 v1∪holdout∪P1∪independent）。"""
    # 1) 禁词
    ban_hits = []
    texts = []
    for ep in episodes:
        for st in ep["steps"]:
            texts.append(st["instruction"])
        proj = OUT / ep["id"] / "project"
        for f in proj.rglob("*"):
            if f.is_file() and f.suffix in {".py", ".md", ".json", ".txt"}:
                try:
                    texts.append(f.read_text(encoding="utf-8"))
                except OSError:
                    pass
    for t in texts:
        for w in FORBIDDEN:
            if re.search(re.escape(w), t, re.I):
                ban_hits.append(w)

    # 2) 指令包含：dose 指令是否包含既有集指令，或反向
    old_instr: list[str] = []
    for jp in [
        P1 / "tasks" / "tasks_v1.0.json",
        P1 / "tasks_v13_holdout" / "holdout_tasks.json",
        P1 / "tasks_p1_validation" / "p1_tasks.json",
        P1 / "tasks_independent_v1" / "independent_tasks.json",
    ]:
        if jp.exists():
            d = json.loads(jp.read_text(encoding="utf-8"))
            for e in d.get("episodes", []):
                for st in e.get("steps", []):
                    old_instr.append(st.get("instruction", ""))
    contain = []
    for ep in episodes:
        for st in ep["steps"]:
            ins = st["instruction"]
            for o in old_instr:
                if o and (o in ins or ins in o):
                    contain.append({"dose": ins[:60], "old": o[:60]})
                    break

    # 3) 文件 sha 交集
    def collect_shas(root: Path) -> set[str]:
        shas = set()
        if not root.exists():
            return shas
        for f in root.rglob("*"):
            if f.is_file() and f.suffix == ".py" and "eval" not in f.parts and "reference" not in f.parts:
                try:
                    shas.add(_sha(f))
                except OSError:
                    pass
        return shas

    dose_shas = collect_shas(OUT)
    old_shas: set[str] = set()
    for root in [
        P1 / "tasks",
        P1 / "tasks_v13_holdout",
        P1 / "tasks_p1_validation",
        P1 / "tasks_independent_v1",
    ]:
        old_shas |= collect_shas(root)
    sha_overlap = dose_shas & old_shas

    # 集内指令唯一
    all_ins = [st["instruction"] for ep in episodes for st in ep["steps"]]
    dup = len(all_ins) - len(set(all_ins))

    audit = {
        "forbidden_hits": sorted(set(ban_hits)),
        "forbidden_pass": len(ban_hits) == 0,
        "instruction_containment": contain,
        "containment_pass": len(contain) == 0,
        "file_sha_overlap": len(sha_overlap),
        "sha_pass": len(sha_overlap) == 0,
        "intra_dup_instructions": dup,
        "intra_unique_pass": dup == 0,
        "n_dose_tasks": len(episodes),
        "n_dose_steps": sum(len(e["steps"]) for e in episodes),
    }
    audit["overall_pass"] = all(
        audit[k]
        for k in ("forbidden_pass", "containment_pass", "sha_pass", "intra_unique_pass")
    )
    return audit


def main() -> int:
    mat = materialize()
    print("discrimination problems:", mat["problems"])
    audit = leakage_audit(mat["episodes"])
    (OUT / "leakage_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    ok = not mat["problems"] and audit["overall_pass"]
    print("OVERALL", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
