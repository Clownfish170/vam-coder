#!/usr/bin/env python
"""生成 V1.3A_CR 本地筛选任务集：6 任务 × 5 步。

场景映射（全部含 step1 相关非目标 FULL 剂量）:
  sc01 跨轮复用 · sc02 常量版本更新 · sc03 相似内容
  sc04 版本更新驱动 · sc05 局部符号 · sc06 无关过滤

判别性：ref_i 过 eval_i；ref_{i-1} 败 eval_i（step1 用 project）。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # p1/
OUT = ROOT / "tasks_v13a_screen"


def write_tree(base: Path, files: dict[str, str]) -> None:
    if base.exists():
        shutil.rmtree(base)
    for rel, body in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def task_sc01() -> dict:
    tid = "sc01_reuse"
    project = {
        "engine.py": (
            "from rates import RATE\n\n\n"
            "def apply(v):\n    return v + RATE\n\n\n"
            "def clamp(x):\n    return max(0, x)\n"
        ),
        # >160B：多函数，紧凑可省；step1 正向参考 rates.py → related 剂量
        "rates.py": (
            "RATE = 3\n"
            "LABEL = 'sc01'\n"
            "TABLE = {'a': 1, 'b': 2, 'c': 3}\n\n\n"
            "def lookup(key):\n    return TABLE.get(key, 0)\n\n\n"
            "def bulk_lookup(keys):\n    return [lookup(k) for k in keys]\n\n\n"
            "def dump_table():\n    return dict(TABLE)\n\n\n"
            "def reset_table():\n    TABLE.clear()\n    TABLE.update({'a': 1, 'b': 2, 'c': 3})\n"
        ),
        "noise.py": "def unused_noise():\n    return 999\n",
    }
    steps = [
        {"id": "step1", "instruction": "请参考 rates.py 中的 RATE 定义。修改 engine.py 中的 apply(v)：结果应为 v * RATE（当前为相加）。不要修改 rates.py。", "eval": "eval/step1"},
        {"id": "step2", "instruction": "请参考 rates.py 中的 RATE 定义。修改 engine.py 中的 clamp(x)：应返回 min(100, max(0, x))。不要修改 rates.py。", "eval": "eval/step2"},
        {"id": "step3", "instruction": "请参考 rates.py 中的 RATE 定义。请在 engine.py 新增 scale(v) 返回 apply(v) * 2。不要修改 rates.py 与 noise.py。", "eval": "eval/step3"},
        {"id": "step4", "instruction": "请参考 rates.py 中的 RATE 定义。修改 engine.py 中的 scale(v)：改为返回 apply(v) + 1。不要修改 rates.py。", "eval": "eval/step4"},
        {"id": "step5", "instruction": "请参考 rates.py 中的 RATE 定义。修改 engine.py 中的 apply(v)：当 v < 0 时返回 0，否则 v * RATE。不要修改 rates.py。", "eval": "eval/step5"},
    ]
    refs = {
        "step1": {
            "engine.py": (
                "from rates import RATE\n\n\n"
                "def apply(v):\n    return v * RATE\n\n\n"
                "def clamp(x):\n    return max(0, x)\n"
            )
        },
        "step2": {
            "engine.py": (
                "from rates import RATE\n\n\n"
                "def apply(v):\n    return v * RATE\n\n\n"
                "def clamp(x):\n    return min(100, max(0, x))\n"
            )
        },
        "step3": {
            "engine.py": (
                "from rates import RATE\n\n\n"
                "def apply(v):\n    return v * RATE\n\n\n"
                "def clamp(x):\n    return min(100, max(0, x))\n\n\n"
                "def scale(v):\n    return apply(v) * 2\n"
            )
        },
        "step4": {
            "engine.py": (
                "from rates import RATE\n\n\n"
                "def apply(v):\n    return v * RATE\n\n\n"
                "def clamp(x):\n    return min(100, max(0, x))\n\n\n"
                "def scale(v):\n    return apply(v) + 1\n"
            )
        },
        "step5": {
            "engine.py": (
                "from rates import RATE\n\n\n"
                "def apply(v):\n    if v < 0:\n        return 0\n    return v * RATE\n\n\n"
                "def clamp(x):\n    return min(100, max(0, x))\n\n\n"
                "def scale(v):\n    return apply(v) + 1\n"
            )
        },
    }
    evals = {
        "step1": "def test_apply():\n    from engine import apply\n    assert apply(4) == 12\n",
        "step2": "def test_clamp():\n    from engine import clamp\n    assert clamp(50) == 50\n    assert clamp(200) == 100\n    assert clamp(-5) == 0\n",
        "step3": "def test_scale():\n    from engine import scale\n    assert scale(4) == 24\n",
        "step4": "def test_scale():\n    from engine import scale\n    assert scale(4) == 13\n",
        "step5": "def test_apply_neg():\n    from engine import apply\n    assert apply(-1) == 0\n    assert apply(4) == 12\n",
    }
    return _pack(tid, project, steps, refs, evals)


def task_sc02() -> dict:
    tid = "sc02_const_version"
    project = {
        "app.py": (
            "from config_consts import MARGIN\n\n\n"
            "def price(x):\n    return x * (1 + MARGIN)\n\n\n"
            "def fee(x):\n    return x + MARGIN\n"
        ),
        "config_consts.py": (
            "MARGIN = 0.10\n"
            "NAME = 'sc02'\n"
            "CAPS = {'max_n': 100, 'min_n': 0}\n\n\n"
            "def get_margin():\n    return MARGIN\n\n\n"
            "def get_caps():\n    return dict(CAPS)\n\n\n"
            "def describe():\n    return f'{NAME}:margin={MARGIN}'\n"
        ),
        "unused.py": "def never():\n    return None\n",
    }
    steps = [
        {"id": "step1", "instruction": "请参考 config_consts.py 中的 MARGIN 定义。修改 app.py 中的 fee(x)：返回 x + MARGIN * 10。不要修改 config_consts.py。", "eval": "eval/step1"},
        {"id": "step2", "instruction": "请参考 app.py 当前实现。修改 config_consts.py 中 MARGIN 为 0.20（当前 0.10）。不要修改 app.py。", "eval": "eval/step2"},
        {"id": "step3", "instruction": "请参考 config_consts.py 中的 MARGIN 定义。修改 app.py 中的 price(x)：返回 x * (1 + MARGIN) * 2。不要修改 config_consts.py。", "eval": "eval/step3"},
        {"id": "step4", "instruction": "请参考 config_consts.py 中的 MARGIN 定义。请在 app.py 新增 total(xs) 返回 sum(price(x) for x in xs)。不要修改 config_consts.py。", "eval": "eval/step4"},
        {"id": "step5", "instruction": "请参考 config_consts.py 中的 MARGIN 定义。修改 app.py 中的 fee(x)：返回 x + MARGIN（去掉 *10）。不要修改 config_consts.py。", "eval": "eval/step5"},
    ]
    refs = {
        "step1": {
            "app.py": (
                "from config_consts import MARGIN\n\n\n"
                "def price(x):\n    return x * (1 + MARGIN)\n\n\n"
                "def fee(x):\n    return x + MARGIN * 10\n"
            )
        },
        "step2": {
            "config_consts.py": (
                "MARGIN = 0.20\n"
                "NAME = 'sc02'\n"
                "CAPS = {'max_n': 100, 'min_n': 0}\n\n\n"
                "def get_margin():\n    return MARGIN\n\n\n"
                "def get_caps():\n    return dict(CAPS)\n\n\n"
                "def describe():\n    return f'{NAME}:margin={MARGIN}'\n"
            )
        },
        "step3": {
            "app.py": (
                "from config_consts import MARGIN\n\n\n"
                "def price(x):\n    return x * (1 + MARGIN) * 2\n\n\n"
                "def fee(x):\n    return x + MARGIN * 10\n"
            )
        },
        "step4": {
            "app.py": (
                "from config_consts import MARGIN\n\n\n"
                "def price(x):\n    return x * (1 + MARGIN) * 2\n\n\n"
                "def fee(x):\n    return x + MARGIN * 10\n\n\n"
                "def total(xs):\n    return sum(price(x) for x in xs)\n"
            )
        },
        "step5": {
            "app.py": (
                "from config_consts import MARGIN\n\n\n"
                "def price(x):\n    return x * (1 + MARGIN) * 2\n\n\n"
                "def fee(x):\n    return x + MARGIN\n\n\n"
                "def total(xs):\n    return sum(price(x) for x in xs)\n"
            )
        },
    }
    evals = {
        "step1": "def test_fee():\n    from app import fee\n    assert abs(fee(1) - 2.0) < 1e-9\n",
        "step2": "def test_margin():\n    from config_consts import MARGIN\n    assert abs(MARGIN - 0.20) < 1e-9\n",
        "step3": "def test_price():\n    from app import price\n    assert abs(price(10) - 10 * 1.2 * 2) < 1e-9\n",
        "step4": "def test_total():\n    from app import total\n    assert total([1, 2]) > 0\n",
        "step5": "def test_fee():\n    from app import fee\n    assert abs(fee(1) - 1.2) < 1e-9\n",
    }
    return _pack(tid, project, steps, refs, evals)


def task_sc03() -> dict:
    tid = "sc03_similar"
    project = {
        "target.py": "def calc(n):\n    return n + 1\n",
        "copy_a.py": (
            "def helper(x):\n    return x * 2\n\n\n"
            "def helper_sum(xs):\n    return sum(helper(x) for x in xs)\n\n\n"
            "def helper_avg(xs):\n    return helper_sum(xs) / max(1, len(xs))\n\n\n"
            "def helper_max(xs):\n    return max(xs) if xs else 0\n"
        ),
        "copy_b.py": (
            "def helper(x):\n    return x  * 2\n\n\n"
            "def helper_sum(xs):\n    return sum(helper(x) for x in xs)\n\n\n"
            "def helper_avg(xs):\n    return helper_sum(xs) / max(1, len(xs))\n\n\n"
            "def helper_max(xs):\n    return max(xs) if xs else 0\n"
        ),
    }
    steps = [
        {"id": "step1", "instruction": "请参考 copy_a.py 中的 helper 形态。修改 target.py 中的 calc(n)：返回 n + 2。不要修改 copy_a.py。", "eval": "eval/step1"},
        {"id": "step2", "instruction": "请参考 copy_a.py 与 copy_b.py 中的 helper 形态。修改 target.py 中的 calc(n)：返回 n * 2。不要修改 copy_a.py 与 copy_b.py。", "eval": "eval/step2"},
        {"id": "step3", "instruction": "请参考 copy_a.py 中的 helper 形态。请在 target.py 新增 double(n) 返回 calc(n) * 2。不要修改 copy_a.py。", "eval": "eval/step3"},
        {"id": "step4", "instruction": "请参考 copy_a.py 中的 helper 形态。修改 target.py 中的 double(n)：改为返回 calc(n) * 3（当前 *2）。不要修改 copy 文件。", "eval": "eval/step4"},
        {"id": "step5", "instruction": "请参考 copy_a.py 中的 helper 形态。修改 target.py 中的 calc(n)：返回 n + 3。不要修改 copy_a.py。", "eval": "eval/step5"},
    ]
    refs = {
        "step1": {"target.py": "def calc(n):\n    return n + 2\n"},
        "step2": {"target.py": "def calc(n):\n    return n * 2\n"},
        "step3": {
            "target.py": (
                "def calc(n):\n    return n * 2\n\n\n"
                "def double(n):\n    return calc(n) * 2\n"
            )
        },
        "step4": {
            "target.py": (
                "def calc(n):\n    return n * 2\n\n\n"
                "def double(n):\n    return calc(n) * 3\n"
            )
        },
        "step5": {
            "target.py": (
                "def calc(n):\n    return n + 3\n\n\n"
                "def double(n):\n    return calc(n) + calc(n)\n"
            )
        },
    }
    evals = {
        "step1": "def test():\n    from target import calc\n    assert calc(1) == 3\n",
        "step2": "def test():\n    from target import calc\n    assert calc(3) == 6\n",
        "step3": "def test():\n    from target import double\n    assert double(3) == 12\n",
        "step4": "def test():\n    from target import double\n    assert double(3) == 18\n",
        "step5": "def test():\n    from target import calc\n    assert calc(1) == 4\n",
    }
    return _pack(tid, project, steps, refs, evals)


def task_sc04() -> dict:
    tid = "sc04_update"
    project = {
        "biz.py": (
            "from taxrate import RATE\n\n\n"
            "def net(x):\n    return x * (1 - RATE)\n"
        ),
        "taxrate.py": (
            "RATE = 0.1\n"
            "NAME = 'standard'\n\n\n"
            "def get_rate():\n    return RATE\n\n\n"
            "def tax_amount(x):\n    return x * RATE\n\n\n"
            "def describe():\n    return f'{NAME}:{RATE}'\n\n\n"
            "def bracket(x):\n    if x < 100:\n        return 'low'\n    return 'high'\n"
        ),
        "pad.py": "def pad():\n    return ''\n",
    }
    steps = [
        {"id": "step1", "instruction": "请参考 taxrate.py 中的 RATE 定义。修改 biz.py 中的 net(x)：返回 x - x * RATE + 1（在原展开式上加 1）。不要修改 taxrate.py。", "eval": "eval/step1"},
        {"id": "step2", "instruction": "请参考 biz.py 当前实现。修改 taxrate.py 中 RATE 为 0.25（当前 0.1）。不要修改 biz.py。", "eval": "eval/step2"},
        {"id": "step3", "instruction": "请参考 taxrate.py 中的 RATE 定义。请在 biz.py 新增 gross(x) 返回 x + x * RATE。不要修改 taxrate.py。", "eval": "eval/step3"},
        {"id": "step4", "instruction": "请参考 taxrate.py 中的 RATE 定义。修改 biz.py 中的 net(x)：当 x <= 0 返回 -1，否则 x - x * RATE + 1。不要修改 taxrate.py。", "eval": "eval/step4"},
        {"id": "step5", "instruction": "请参考 taxrate.py 中的 RATE 定义。修改 biz.py 中的 gross(x)：返回 x * (1 + RATE) * 2（翻倍）。不要修改 taxrate.py。", "eval": "eval/step5"},
    ]
    refs = {
        "step1": {
            "biz.py": (
                "from taxrate import RATE\n\n\n"
                "def net(x):\n    return x - x * RATE + 1\n"
            )
        },
        "step2": {
            "taxrate.py": (
                "RATE = 0.25\n"
                "NAME = 'standard'\n\n\n"
                "def get_rate():\n    return RATE\n\n\n"
                "def tax_amount(x):\n    return x * RATE\n\n\n"
                "def describe():\n    return f'{NAME}:{RATE}'\n\n\n"
                "def bracket(x):\n    if x < 100:\n        return 'low'\n    return 'high'\n"
            )
        },
        "step3": {
            "biz.py": (
                "from taxrate import RATE\n\n\n"
                "def net(x):\n    return x - x * RATE + 1\n\n\n"
                "def gross(x):\n    return x + x * RATE\n"
            )
        },
        "step4": {
            "biz.py": (
                "from taxrate import RATE\n\n\n"
                "def net(x):\n    if x <= 0:\n        return -1\n    return x - x * RATE + 1\n\n\n"
                "def gross(x):\n    return x + x * RATE\n"
            )
        },
        "step5": {
            "biz.py": (
                "from taxrate import RATE\n\n\n"
                "def net(x):\n    if x <= 0:\n        return -1\n    return x - x * RATE + 1\n\n\n"
                "def gross(x):\n    return x * (1 + RATE) * 2\n"
            )
        },
    }
    evals = {
        "step1": "def test():\n    from biz import net\n    assert abs(net(10) - 10.0) < 1e-9\n",
        "step2": "def test():\n    from taxrate import RATE\n    assert abs(RATE - 0.25) < 1e-9\n",
        "step3": "def test():\n    from biz import gross\n    assert abs(gross(10) - 12.5) < 1e-9\n",
        "step4": "def test():\n    from biz import net\n    assert net(0) == -1\n    assert abs(net(10) - 8.5) < 1e-9\n",
        "step5": "def test():\n    from biz import gross\n    assert abs(gross(10) - 25.0) < 1e-9\n",
    }
    return _pack(tid, project, steps, refs, evals)


def task_sc05() -> dict:
    tid = "sc05_range"
    project = {
        "core.py": (
            "def alpha(a):\n    return a + 1\n\n\n"
            "def beta(b):\n    return b + 2\n\n\n"
            "def gamma(g):\n    return g + 3\n"
        ),
        "side.py": (
            "SIDE = 1\n"
            "SIDE_NAME = 'sc05'\n\n\n"
            "def side_fn():\n    return SIDE\n\n\n"
            "def side_label():\n    return SIDE_NAME\n\n\n"
            "def side_scale(x):\n    return x * SIDE\n\n\n"
            "def side_report(x):\n    return f'{SIDE_NAME}:{side_scale(x)}'\n"
        ),
        "junk.py": "def junk():\n    return 0\n",
    }
    steps = [
        {"id": "step1", "instruction": "请参考 side.py 中的 SIDE 定义。修改 core.py 中的 alpha(a)：返回 a + 10。不要修改 side.py。", "eval": "eval/step1"},
        {"id": "step2", "instruction": "请参考 side.py 中的 SIDE 定义。修改 core.py 中的 beta(b)：返回 b * 2。不要修改 side.py。", "eval": "eval/step2"},
        {"id": "step3", "instruction": "请参考 side.py 中的 SIDE 定义。修改 core.py 中的 gamma(g)：返回 g * 3。不要修改 side.py。", "eval": "eval/step3"},
        {"id": "step4", "instruction": "请参考 side.py 中的 SIDE 定义。请在 core.py 新增 delta(d) 返回 alpha(d) + beta(d)。不要修改 side.py。", "eval": "eval/step4"},
        {"id": "step5", "instruction": "请参考 side.py 中的 SIDE 定义。修改 core.py 中的 alpha(a)：当 a < 0 返回 0，否则 a + 10。不要修改 side.py。", "eval": "eval/step5"},
    ]
    refs = {
        "step1": {
            "core.py": (
                "def alpha(a):\n    return a + 10\n\n\n"
                "def beta(b):\n    return b + 2\n\n\n"
                "def gamma(g):\n    return g + 3\n"
            )
        },
        "step2": {
            "core.py": (
                "def alpha(a):\n    return a + 10\n\n\n"
                "def beta(b):\n    return b * 2\n\n\n"
                "def gamma(g):\n    return g + 3\n"
            )
        },
        "step3": {
            "core.py": (
                "def alpha(a):\n    return a + 10\n\n\n"
                "def beta(b):\n    return b * 2\n\n\n"
                "def gamma(g):\n    return g * 3\n"
            )
        },
        "step4": {
            "core.py": (
                "def alpha(a):\n    return a + 10\n\n\n"
                "def beta(b):\n    return b * 2\n\n\n"
                "def gamma(g):\n    return g * 3\n\n\n"
                "def delta(d):\n    return alpha(d) + beta(d)\n"
            )
        },
        "step5": {
            "core.py": (
                "def alpha(a):\n    if a < 0:\n        return 0\n    return a + 10\n\n\n"
                "def beta(b):\n    return b * 2\n\n\n"
                "def gamma(g):\n    return g * 3\n\n\n"
                "def delta(d):\n    return alpha(d) + beta(d)\n"
            )
        },
    }
    evals = {
        "step1": "def test():\n    from core import alpha\n    assert alpha(5) == 15\n",
        "step2": "def test():\n    from core import beta\n    assert beta(4) == 8\n",
        "step3": "def test():\n    from core import gamma\n    assert gamma(2) == 6\n",
        "step4": "def test():\n    from core import delta\n    assert delta(5) == 25\n",
        "step5": "def test():\n    from core import alpha\n    assert alpha(-1) == 0\n    assert alpha(5) == 15\n",
    }
    return _pack(tid, project, steps, refs, evals)


def task_sc06() -> dict:
    tid = "sc06_filter"
    project = {
        "main.py": (
            "from limits import MAX\n\n\n"
            "def clamp(n):\n    return min(n, MAX)\n\n\n"
            "def zero(n):\n    return 0 if n < 0 else n\n"
        ),
        "limits.py": (
            "MAX = 10\n"
            "MIN = 0\n"
            "TAG = 'sc06'\n\n\n"
            "def get_max():\n    return MAX\n\n\n"
            "def get_min():\n    return MIN\n\n\n"
            "def span():\n    return MAX - MIN\n\n\n"
            "def label():\n    return TAG\n"
        ),
        "junk_a.py": "def a():\n    return 'a'\n",
        "junk_b.py": "def b():\n    return 'b'\n",
    }
    steps = [
        {"id": "step1", "instruction": "请参考 limits.py 中的 MAX 定义。修改 main.py 中的 clamp(n)：若 n < 0 返回 0，否则 min(n, MAX)。不要修改 limits.py。", "eval": "eval/step1"},
        {"id": "step2", "instruction": "请参考 main.py 当前实现。修改 limits.py 中 MAX 为 50（当前 10）。不要修改 main.py。", "eval": "eval/step2"},
        {"id": "step3", "instruction": "请参考 limits.py 中的 MAX 定义。修改 main.py 中的 zero(n)：返回 -1 if n == 0 else (0 if n < 0 else n)。不要修改 limits.py。", "eval": "eval/step3"},
        {"id": "step4", "instruction": "请参考 limits.py 中的 MAX 定义。请在 main.py 新增 bounded(n) 返回 clamp(zero(n))。不要修改 limits.py 与 junk 文件。", "eval": "eval/step4"},
        {"id": "step5", "instruction": "请参考 limits.py 中的 MAX 定义。修改 main.py 中的 bounded(n)：返回 zero(clamp(n))（交换组合顺序）。不要修改 limits.py。", "eval": "eval/step5"},
    ]
    refs = {
        "step1": {
            "main.py": (
                "from limits import MAX\n\n\n"
                "def clamp(n):\n    if n < 0:\n        return 0\n    return min(n, MAX)\n\n\n"
                "def zero(n):\n    return 0 if n < 0 else n\n"
            )
        },
        "step2": {
            "limits.py": (
                "MAX = 50\n"
                "MIN = 0\n"
                "TAG = 'sc06'\n\n\n"
                "def get_max():\n    return MAX\n\n\n"
                "def get_min():\n    return MIN\n\n\n"
                "def span():\n    return MAX - MIN\n\n\n"
                "def label():\n    return TAG\n"
            )
        },
        "step3": {
            "main.py": (
                "from limits import MAX\n\n\n"
                "def clamp(n):\n    if n < 0:\n        return 0\n    return min(n, MAX)\n\n\n"
                "def zero(n):\n    if n == 0:\n        return -1\n    return 0 if n < 0 else n\n"
            )
        },
        "step4": {
            "main.py": (
                "from limits import MAX\n\n\n"
                "def clamp(n):\n    if n < 0:\n        return 0\n    return min(n, MAX)\n\n\n"
                "def zero(n):\n    if n == 0:\n        return -1\n    return 0 if n < 0 else n\n\n\n"
                "def bounded(n):\n    return clamp(zero(n))\n"
            )
        },
        "step5": {
            "main.py": (
                "from limits import MAX\n\n\n"
                "def clamp(n):\n    if n < 0:\n        return 0\n    return min(n, MAX)\n\n\n"
                "def zero(n):\n    if n == 0:\n        return -1\n    return 0 if n < 0 else n\n\n\n"
                "def bounded(n):\n    return zero(clamp(n))\n"
            )
        },
    }
    evals = {
        "step1": "def test():\n    from main import clamp\n    assert clamp(-1) == 0\n    assert clamp(100) == 10\n",
        "step2": "def test():\n    from limits import MAX\n    assert MAX == 50\n",
        "step3": "def test():\n    from main import zero\n    assert zero(0) == -1\n    assert zero(3) == 3\n",
        "step4": "def test():\n    from main import bounded\n    assert bounded(0) == 0\n    assert bounded(100) == 50\n",
        "step5": "def test():\n    from main import bounded\n    assert bounded(0) == -1\n    assert bounded(100) == 50\n",
    }
    return _pack(tid, project, steps, refs, evals)


def _pack(tid, project, steps, refs, evals) -> dict:
    return {"id": tid, "steps": steps, "_project": project, "_refs": refs, "_evals": evals}


def _run_eval(tree: Path, ev: Path) -> int:
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


def materialize() -> list[str]:
    tasks = [
        task_sc01(),
        task_sc02(),
        task_sc03(),
        task_sc04(),
        task_sc05(),
        task_sc06(),
    ]
    if OUT.exists():
        for child in list(OUT.iterdir()):
            if child.name == "make_screen_tasks.py":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    OUT.mkdir(parents=True, exist_ok=True)

    episodes = []
    for ep in tasks:
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

    problems: list[str] = []
    for ep in tasks:
        tid = ep["id"]
        steps = ep["steps"]
        for i, step in enumerate(steps):
            sid = step["id"]
            ev = OUT / tid / "eval" / sid / "test_behavior.py"
            ref = OUT / tid / "reference" / sid
            if _run_eval(ref, ev) != 0:
                problems.append(f"{tid}/{sid} reference FAIL")
            prev = OUT / tid / "reference" / steps[i - 1]["id"] if i > 0 else OUT / tid / "project"
            if _run_eval(prev, ev) == 0:
                problems.append(f"{tid}/{sid} prev PASS (want FAIL)")

    payload = {
        "schema": "v13a-screen-tasks-v1",
        "episodes": episodes,
        "discrimination_problems": problems,
    }
    (OUT / "v13a_screen_tasks.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {OUT} tasks={len(episodes)} problems={len(problems)}")
    for p in problems:
        print(" PROBLEM", p)
    return problems


if __name__ == "__main__":
    probs = materialize()
    raise SystemExit(1 if probs else 0)
