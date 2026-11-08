#!/usr/bin/env python
"""按 rev3.2 规范一次性生成 P1-v1.0 任务树（可重复运行；输出与磁盘一致）。

生成物（不覆盖 v0.2）：
  p1/tasks/tasks_v1.0.json
  p1/tasks/predeclared_mechanisms_v1.0.json
  p1/tasks/v1_<ID>/{project,reference/stepN,eval/stepN}
运行后由 selfcheck_v1.py 独立验证行为正确性。
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parent.parent
TASKS = P1_ROOT / "tasks"

# 每任务：project 文件、s1/s2 指令、reference 补丁（变更文件全文）、eval 源码
T: dict[str, dict] = {}


def task(tid, focus, s1, s2, project, ref1, ref2, ev1, ev2, note=""):
    T[tid] = dict(
        focus=focus, s1=s1, s2=s2, project=project,
        ref1=ref1, ref2=ref2, ev1=ev1, ev2=ev2, note=note,
    )


# ---------- CFD ----------
task(
    "CFD01", "cross_file_dep",
    "tax_rate() 的税率应为 0.5。请修改 tax.py 中的返回值。",
    "在 invoice.py 中新增 net_total(cents)，返回不含税金额 int(cents/(1+tax_rate()))。",
    {
        "tax.py": '"""Tax helpers."""\n\n\ndef tax_rate():\n    """Current tax rate."""\n    return 0.25\n',
        "invoice.py": "from tax import tax_rate\n\n\ndef grand_total(cents):\n    return int(cents * (1 + tax_rate()))\n",
    },
    {"tax.py": '"""Tax helpers."""\n\n\ndef tax_rate():\n    """Current tax rate."""\n    return 0.5\n'},
    {"invoice.py": "from tax import tax_rate\n\n\ndef grand_total(cents):\n    return int(cents * (1 + tax_rate()))\n\n\ndef net_total(cents):\n    return int(cents / (1 + tax_rate()))\n"},
    "import tax, invoice\n\n\ndef test_rate():\n    assert tax.tax_rate() == 0.5\n\n\ndef test_grand():\n    assert invoice.grand_total(1000) == 1500\n",
    "import invoice\n\n\ndef test_net():\n    assert invoice.net_total(1500) == 1000\n\n\ndef test_grand_still():\n    assert invoice.grand_total(1500) == 2250\n",
)
task(
    "CFD02", "cross_file_dep",
    "fee() 的乘数应为 5。请修改 rates.py 中 fee 的实现。",
    "为性能新增 cost_fast(qty)（order.py）：写死当前乘数 5 计算 qty*5+1，禁止调用 fee()。",
    {
        "rates.py": "STANDARD = 3\n\n\ndef fee(qty):\n    return qty * STANDARD\n",
        "order.py": "from rates import fee\n\n\ndef cost(qty):\n    return fee(qty) + 1\n",
    },
    {"rates.py": "STANDARD = 3\n\n\ndef fee(qty):\n    return qty * 5\n"},
    {"order.py": "from rates import fee\n\n\ndef cost(qty):\n    return fee(qty) + 1\n\n\ndef cost_fast(qty):\n    return qty * 5 + 1\n"},
    "import order\n\n\ndef test_cost():\n    assert order.cost(2) == 11\n",
    "import order\n\n\ndef test_cost_fast():\n    assert order.cost_fast(2) == 11\n\n\ndef test_cost():\n    assert order.cost(2) == 11\n",
)
task(
    "CFD03", "cross_file_dep",
    "clamp 在 lo>hi 时应抛出 ValueError。请在 util.py 增加该校验。",
    "在 app.py 新增 batch(vals)：返回 [norm(v) for v in vals]。",
    {
        "util.py": "def clamp(x, lo, hi):\n    return max(lo, min(hi, x))\n",
        "app.py": "from util import clamp\n\n\ndef norm(x):\n    return clamp(x, 0, 10)\n",
    },
    {"util.py": "def clamp(x, lo, hi):\n    if lo > hi:\n        raise ValueError(\"lo > hi\")\n    return max(lo, min(hi, x))\n"},
    {"app.py": "from util import clamp\n\n\ndef norm(x):\n    return clamp(x, 0, 10)\n\n\ndef batch(vals):\n    return [norm(v) for v in vals]\n"},
    "import pytest, util\n\n\ndef test_clamp_ok():\n    assert util.clamp(1, 0, 10) == 1\n\n\ndef test_clamp_raises():\n    with pytest.raises(ValueError):\n        util.clamp(1, 5, 0)\n",
    "import app\n\n\ndef test_batch():\n    assert app.batch([-1, 5]) == [0, 5]\n",
)
# ---------- SIG ----------
task(
    "SIG01", "signature_change",
    "wrap 的参数顺序改为 (width, s)。请同步所有调用方。",
    "show 应使用宽度 20。",
    {
        "text.py": "def wrap(s, width):\n    return s[:width]\n",
        "cli.py": "from text import wrap\n\n\ndef show(s):\n    return wrap(s, 10)\n",
    },
    {"text.py": "def wrap(width, s):\n    return s[:width]\n",
     "cli.py": "from text import wrap\n\n\ndef show(s):\n    return wrap(10, s)\n"},
    {"cli.py": "from text import wrap\n\n\ndef show(s):\n    return wrap(20, s)\n"},
    "import text, cli\n\n\ndef test_wrap():\n    assert text.wrap(3, 'abcdef') == 'abc'\n\n\ndef test_show():\n    assert cli.show('x' * 30) == 'x' * 10\n",
    "import cli\n\n\ndef test_show20():\n    assert cli.show('y' * 30) == 'y' * 20\n",
)
task(
    "SIG02", "signature_change",
    "area 改为接受单个元组 area(dim)，dim=(w,h)。更新调用方。",
    "report.py 新增 total(dims)：dims 为元组列表，返回面积之和。",
    {
        "geom.py": "def area(w, h):\n    return w * h\n",
        "report.py": "from geom import area\n\n\ndef line(w, h):\n    return f\"{area(w, h)} u2\"\n",
    },
    {"geom.py": "def area(dim):\n    w, h = dim\n    return w * h\n",
     "report.py": "from geom import area\n\n\ndef line(w, h):\n    return f\"{area((w, h))} u2\"\n"},
    {"report.py": "from geom import area\n\n\ndef line(w, h):\n    return f\"{area((w, h))} u2\"\n\n\ndef total(dims):\n    return sum(area(d) for d in dims)\n"},
    "import geom, report\n\n\ndef test_area():\n    assert geom.area((3, 4)) == 12\n\n\ndef test_line():\n    assert report.line(3, 4) == '12 u2'\n",
    "import report\n\n\ndef test_total():\n    assert report.total([(3, 4), (2, 2)]) == 16\n",
)
task(
    "SIG03", "signature_change",
    "put 改为返回写入后的值 v（不再返回 d）。更新调用方使 seed() 仍返回完整字典。",
    "use.py 新增 seed_b()：写入 'a'=2 与 'b'=3 并返回字典。",
    {
        "store.py": "def put(d, k, v):\n    d[k] = v\n    return d\n",
        "use.py": "from store import put\n\n\ndef seed():\n    d = {}\n    put(d, 'a', 1)\n    return d\n",
    },
    {"store.py": "def put(d, k, v):\n    d[k] = v\n    return v\n",
     "use.py": "from store import put\n\n\ndef seed():\n    d = {}\n    put(d, 'a', 1)\n    return d\n"},
    {"use.py": "from store import put\n\n\ndef seed():\n    d = {}\n    put(d, 'a', 1)\n    return d\n\n\ndef seed_b():\n    d = {}\n    put(d, 'a', 2)\n    put(d, 'b', 3)\n    return d\n"},
    "import store, use\n\n\ndef test_put():\n    assert store.put({}, 'k', 1) == 1\n\n\ndef test_seed():\n    assert use.seed() == {'a': 1}\n",
    "import use\n\n\ndef test_seed_b():\n    assert use.seed_b() == {'a': 2, 'b': 3}\n",
)
# ---------- REN ----------
task(
    "REN01", "rename_tombstone",
    "将 double 重命名为 double_value，更新所有调用方，不要保留旧名。",
    "bump 现在应返回 double_value(x)+3。",
    {
        "core.py": '"""Core helpers."""\n\n\ndef double(x):\n    """Double x."""\n    return x * 2\n\n\ndef bump(x):\n    return double(x) + 1\n',
        "main.py": "from core import bump\n\n\ndef run(x):\n    return bump(x)\n",
    },
    {"core.py": '"""Core helpers."""\n\n\ndef double_value(x):\n    """Double x."""\n    return x * 2\n\n\ndef bump(x):\n    return double_value(x) + 1\n'},
    {"core.py": '"""Core helpers."""\n\n\ndef double_value(x):\n    """Double x."""\n    return x * 2\n\n\ndef bump(x):\n    return double_value(x) + 3\n'},
    "import core, main\n\n\ndef test_double_value():\n    assert core.double_value(4) == 8\n\n\ndef test_old_gone():\n    assert not hasattr(core, 'double')\n\n\ndef test_bump():\n    assert core.bump(4) == 9\n\n\ndef test_run():\n    assert main.run(4) == 9\n",
    "import core, main\n\n\ndef test_bump3():\n    assert core.bump(4) == 11\n\n\ndef test_run3():\n    assert main.run(4) == 11\n",
    note="S8: rev3.2 表中 step1 eval 曾写 bump(4)==11，与“step2 才改 +3”矛盾；以行为链为准：step1 期望 9。",
)
task(
    "REN02", "rename_tombstone",
    "将 Client.fetch 重命名为 Client.request，更新调用方。",
    "request 应返回 f\"GET2:{url}\"。",
    {
        "api.py": "class Client:\n    def fetch(self, url):\n        return f\"GET:{url}\"\n",
        "app.py": "from api import Client\n\n\ndef go():\n    return Client().fetch('u')\n",
    },
    {"api.py": "class Client:\n    def request(self, url):\n        return f\"GET:{url}\"\n",
     "app.py": "from api import Client\n\n\ndef go():\n    return Client().request('u')\n"},
    {"api.py": "class Client:\n    def request(self, url):\n        return f\"GET2:{url}\"\n"},
    "import api, app\n\n\ndef test_request():\n    assert api.Client().request('u') == 'GET:u'\n\n\ndef test_fetch_gone():\n    assert not hasattr(api.Client, 'fetch')\n\n\ndef test_go():\n    assert app.go() == 'GET:u'\n",
    "import api\n\n\ndef test_get2():\n    assert api.Client().request('u') == 'GET2:u'\n",
)
# ---------- DEL ----------
task(
    "DEL01", "delete_tombstone",
    "删除 lib.py 中的 dead()。",
    "app.py 新增 twice_keep()：返回 keep() 的二倍。",
    {
        "lib.py": "def keep():\n    return 21\n\n\ndef dead():\n    return 0\n",
        "app.py": "from lib import keep\n\n\ndef use():\n    return keep()\n",
    },
    {"lib.py": "def keep():\n    return 21\n"},
    {"app.py": "from lib import keep\n\n\ndef use():\n    return keep()\n\n\ndef twice_keep():\n    return keep() * 2\n"},
    "import lib, app\n\n\ndef test_dead_gone():\n    assert not hasattr(lib, 'dead')\n\n\ndef test_keep():\n    assert lib.keep() == 21\n",
    "import app\n\n\ndef test_twice():\n    assert app.twice_keep() == 42\n",
)
task(
    "DEL02", "delete_tombstone",
    "删除 queue.py 中未被 worker.py 使用的函数。",
    "worker.py 新增 drain(items)：循环 p() 直到列表为空，返回弹出元素个数。",
    {
        "queue.py": "def push(items, x):\n    items.append(x)\n    return items\n\n\ndef q():\n    return []\n\n\ndef p(items):\n    return items.pop()\n",
        "worker.py": "from queue import push, p\n\n\ndef work(items, x):\n    push(items, x)\n    return p(items)\n",
    },
    {"queue.py": "def push(items, x):\n    items.append(x)\n    return items\n\n\ndef p(items):\n    return items.pop()\n"},
    {"worker.py": "from queue import push, p\n\n\ndef work(items, x):\n    push(items, x)\n    return p(items)\n\n\ndef drain(items):\n    count = 0\n    while items:\n        p(items)\n        count += 1\n    return count\n"},
    "import queue as qmod\n\n\ndef test_q_gone():\n    assert not hasattr(qmod, 'q')\n\n\ndef test_p_exists():\n    assert hasattr(qmod, 'p')\n",
    "import worker\n\n\ndef test_drain():\n    items = [1, 2, 3]\n    assert worker.drain(items) == 3\n    assert items == []\n",
)
# ---------- DUP ----------
task(
    "DUP01", "disambiguation",
    "mathx.norm 应返回 x/4。不要改 textx。",
    "textx 新增 norm2(s)：返回 norm(s).upper()（textx 的 norm）。",
    {
        "mathx.py": "def norm(x):\n    return x / 2\n",
        "textx.py": "def norm(s):\n    return s.strip()\n",
    },
    {"mathx.py": "def norm(x):\n    return x / 4\n"},
    {"textx.py": "def norm(s):\n    return s.strip()\n\n\ndef norm2(s):\n    return norm(s).upper()\n"},
    "import mathx, textx\n\n\ndef test_mathx():\n    assert mathx.norm(8) == 2\n\n\ndef test_textx():\n    assert textx.norm(' a ') == 'a'\n",
    "import textx\n\n\ndef test_norm2():\n    assert textx.norm2(' a ') == 'A'\n",
)
task(
    "DUP02", "disambiguation",
    "conf.apply 应返回 x*3。请修改 conf.py 中 apply 的实现（可保留或删除 RATE 常量）。",
    "新增 conf2.apply3(x)：使用 conf 当前乘数 3 与 conf2 的加法规则组合：x*3+conf2.RATE。允许 import conf。",
    {
        "conf.py": "RATE = 2\n\n\ndef apply(x):\n    return x * RATE\n",
        "conf2.py": "RATE = 5\n\n\ndef apply(x):\n    return x + RATE\n",
    },
    {"conf.py": "RATE = 2\n\n\ndef apply(x):\n    return x * 3\n"},
    {"conf2.py": "import conf\n\nRATE = 5\n\n\ndef apply(x):\n    return x + RATE\n\n\ndef apply3(x):\n    return x * 3 + RATE\n"},
    "import conf, conf2\n\n\ndef test_conf():\n    assert conf.apply(2) == 6\n\n\ndef test_conf2():\n    assert conf2.apply(2) == 7\n",
    "import conf2\n\n\ndef test_apply3():\n    assert conf2.apply3(2) == 11\n",
)
# ---------- IRR ----------
task(
    "IRR01", "irrelevant_change",
    "只修改 alpha.py：a() 返回 10。",
    "只新增 alpha.py 的 a2() 返回 a()+1。不要修改 beta.py。",
    {
        "alpha.py": "def a():\n    return 1\n",
        "beta.py": "def b():\n    return 2\n",
    },
    {"alpha.py": "def a():\n    return 10\n"},
    {"alpha.py": "def a():\n    return 10\n\n\ndef a2():\n    return a() + 1\n"},
    "import alpha, beta\n\n\ndef test_a():\n    assert alpha.a() == 10\n\n\ndef test_b_untouched():\n    assert beta.b() == 2\n",
    "import alpha, beta\n\n\ndef test_a2():\n    assert alpha.a2() == 11\n\n\ndef test_b():\n    assert beta.b() == 2\n",
)
task(
    "IRR02", "irrelevant_change",
    "修改 helpers.h2 的返回值为 20。不要动其他文件。",
    "删除 scratch.py。",
    {
        "main.py": "from helpers import h1\n\n\ndef run():\n    return h1()\n",
        "helpers.py": "def h1():\n    return 1\n\n\ndef h2():\n    return 2\n\n\ndef h3():\n    return 3\n",
        "scratch.py": "def tmp():\n    return 0\n",
    },
    {"helpers.py": "def h1():\n    return 1\n\n\ndef h2():\n    return 20\n\n\ndef h3():\n    return 3\n"},
    {},
    "import helpers\n\n\ndef test_h2():\n    assert helpers.h2() == 20\n\n\ndef test_others():\n    assert helpers.h1() == 1 and helpers.h3() == 3\n",
    "import importlib\nimport pytest\n\n\ndef test_scratch_gone():\n    with pytest.raises(ModuleNotFoundError):\n        importlib.import_module('scratch')\n",
)
T["IRR02"]["ref2"] = {"__DELETE__": ["scratch.py"]}
# ---------- CLS ----------
task(
    "CLS01", "dependency_closure",
    "base 应返回 x+2。",
    "top 应改为 mid(x)+20。",
    {
        "low.py": "def base(x):\n    return x + 1\n",
        "mid.py": "from low import base\n\n\ndef mid(x):\n    return base(x) * 2\n",
        "high.py": "from mid import mid\n\n\ndef top(x):\n    return mid(x) + 10\n",
    },
    {"low.py": "def base(x):\n    return x + 2\n"},
    {"high.py": "from mid import mid\n\n\ndef top(x):\n    return mid(x) + 20\n"},
    "import high, mid\n\n\ndef test_mid_step1():\n    assert mid.mid(1) == 6\n\n\ndef test_top_step1():\n    assert high.top(1) == 16\n",
    "import high, mid\n\n\ndef test_mid():\n    assert mid.mid(1) == 6\n\n\ndef test_top():\n    assert high.top(1) == 26\n",
)
task(
    "CLS02", "dependency_closure",
    "convert 应返回 v*3。只修改 hub.py。",
    "b.py 的函数应改为先 convert 再 +1（a/c 不变）。",
    {
        "hub.py": "def convert(v):\n    return v * 2\n",
        "a.py": "from hub import convert\n\n\ndef fa(v):\n    return convert(v)\n",
        "b.py": "from hub import convert\n\n\ndef fb(v):\n    return convert(v)\n",
        "c.py": "from hub import convert\n\n\ndef fc(v):\n    return convert(v)\n",
    },
    {"hub.py": "def convert(v):\n    return v * 3\n"},
    {"b.py": "from hub import convert\n\n\ndef fb(v):\n    return convert(v) + 1\n"},
    "import a, b, c\n\n\ndef test_all_x3():\n    assert a.fa(2) == 6\n    assert b.fb(2) == 6\n    assert c.fc(2) == 6\n",
    "import a, b, c\n\n\ndef test_b_plus1():\n    assert b.fb(2) == 7\n\n\ndef test_ac_unchanged():\n    assert a.fa(2) == 6\n    assert c.fc(2) == 6\n",
)
# ---------- STM ----------
task(
    "STM01", "stale_summary",
    "定价政策变更：UNIT 应为 12。请修改 pricing.py 中的 UNIT，并同步更新 price 的 docstring 中的数值描述。",
    "在 discount.py 新增 fast_price(qty)：写死当前单价数值直接计算（禁止导入常量、禁止调用 price），行为与 price() 完全一致。",
    {
        "pricing.py": '"""Pricing rules."""\n\nUNIT = 10\n\n\ndef price(qty):\n    """Unit price is UNIT (=10) per piece."""\n    return qty * UNIT\n',
        "discount.py": "from pricing import price\n\n\ndef total(qty):\n    return price(qty)\n",
    },
    {"pricing.py": '"""Pricing rules."""\n\nUNIT = 12\n\n\ndef price(qty):\n    """Unit price is UNIT (=12) per piece."""\n    return qty * UNIT\n'},
    {"discount.py": "from pricing import price\n\n\ndef total(qty):\n    return price(qty)\n\n\ndef fast_price(qty):\n    return qty * 12\n"},
    "import pricing\n\n\ndef test_price():\n    assert pricing.price(3) == 36\n",
    "import pricing, discount\n\n\ndef test_price():\n    assert pricing.price(3) == 36\n\n\ndef test_fast():\n    assert discount.fast_price(3) == 36\n    assert discount.fast_price(10) == 120\n\n\ndef test_total():\n    assert discount.total(3) == 36\n",
)
task(
    "STM02", "stale_summary",
    "服务费公式改为 qty*6。请更新 fee.py 中 service 的实现与 docstring 描述。",
    "bill.py 新增 due_fast(qty)：写死当前公式（禁止调用 service），与 due() 行为一致。",
    {
        "fee.py": '"""Fees."""\n\n\ndef service(qty):\n    """Service fee = qty * 4."""\n    return qty * 4\n',
        "bill.py": "from fee import service\n\n\ndef due(qty):\n    return service(qty) + 1\n",
    },
    {"fee.py": '"""Fees."""\n\n\ndef service(qty):\n    """Service fee = qty * 6."""\n    return qty * 6\n'},
    {"bill.py": "from fee import service\n\n\ndef due(qty):\n    return service(qty) + 1\n\n\ndef due_fast(qty):\n    return qty * 6 + 1\n"},
    "import bill\n\n\ndef test_due():\n    assert bill.due(2) == 13\n",
    "import bill\n\n\ndef test_due_fast():\n    assert bill.due_fast(2) == 13\n\n\ndef test_due():\n    assert bill.due(2) == 13\n",
)
task(
    "STM03", "stale_summary_exploratory",
    "apply_tier 的 gold 乘数应为 9。请修改 ratemap.py 中 apply_tier 的实现（可保留或删除 GOLD 常量）。legacy_notes.py 是废弃说明，按现状保留即可。",
    "shop.py 新增 quote_fast(x)：写死当前 gold 乘数（禁止调用 apply_tier），与 quote() 行为一致。",
    {
        "ratemap.py": '"""Rate map."""\n\nGOLD = 7\n\n\ndef apply_tier(x, tier):\n    """Apply tier multiplier."""\n    return x * (GOLD if tier == "gold" else 1)\n',
        "legacy_notes.py": '"""Deprecated notes: gold multiplier is 5 (deprecated)."""\n\nNOTES = "gold multiplier is 5 (deprecated)"\n',
        "shop.py": "from ratemap import apply_tier\n\n\ndef quote(x):\n    return apply_tier(x, 'gold')\n",
    },
    {"ratemap.py": '"""Rate map."""\n\nGOLD = 7\n\n\ndef apply_tier(x, tier):\n    """Apply tier multiplier."""\n    return x * (9 if tier == "gold" else 1)\n'},
    {"shop.py": "from ratemap import apply_tier\n\n\ndef quote(x):\n    return apply_tier(x, 'gold')\n\n\ndef quote_fast(x):\n    return x * 9\n"},
    "import ratemap, shop\n\n\ndef test_quote():\n    assert shop.quote(2) == 18\n\n\ndef test_apply_tier():\n    assert ratemap.apply_tier(2, 'gold') == 18\n",
    "import shop\n\n\ndef test_quote_fast():\n    assert shop.quote_fast(2) == 18\n\n\ndef test_quote():\n    assert shop.quote(2) == 18\n",
)
# ---------- RFS ----------
task(
    "RFS01", "refresh_control",
    "当前模式应为 active。请修改 mode.py 中 describe 的返回值，并同步 docstring 中的模式名描述。",
    "app.py 新增 is_active()：当模式为 active 时返回 True。",
    {
        "mode.py": '"""Mode."""\n\n\ndef describe():\n    """Return the active mode name: idle."""\n    return "idle"\n',
        "app.py": "from mode import describe\n\n\ndef banner():\n    return f\"mode={describe()}\"\n",
    },
    {"mode.py": '"""Mode."""\n\n\ndef describe():\n    """Return the active mode name: active."""\n    return "active"\n'},
    {"app.py": "from mode import describe\n\n\ndef banner():\n    return f\"mode={describe()}\"\n\n\ndef is_active():\n    return describe() == 'active'\n"},
    "import app\n\n\ndef test_banner():\n    assert app.banner() == 'mode=active'\n",
    "import app\n\n\ndef test_is_active():\n    assert app.is_active() is True\n\n\ndef test_banner():\n    assert app.banner() == 'mode=active'\n",
)
task(
    "RFS02", "refresh_control",
    "状态码应为 404。请修改 status.py 中 code 的返回值并同步 docstring 描述。",
    "client.py 新增 is_missing()：状态码为 404 时返回 True。",
    {
        "status.py": '"""Status."""\n\n\ndef code():\n    """HTTP-ish code: 200 OK."""\n    return 200\n',
        "client.py": "from status import code\n\n\ndef ok():\n    return code() == 200\n",
    },
    {"status.py": '"""Status."""\n\n\ndef code():\n    """HTTP-ish code: 404 missing."""\n    return 404\n'},
    {"client.py": "from status import code\n\n\ndef ok():\n    return code() == 200\n\n\ndef is_missing():\n    return code() == 404\n"},
    "import client, status\n\n\ndef test_code():\n    assert status.code() == 404\n\n\ndef test_ok_false():\n    assert client.ok() is False\n",
    "import client\n\n\ndef test_is_missing():\n    assert client.is_missing() is True\n",
)
# ---------- RUR ----------
task(
    "RUR01", "reread_required",
    "请修改 tables.py 中 lookup 的实现以支持键 3：lookup(3) 返回 \"c\"，其他键行为不变（未知键仍返回 \"?\"）。",
    "app.py 新增 show3()：返回 lookup(3) 的值（写死 \"c\" 亦可，但必须与当前实现一致）。",
    {
        "tables.py": 'LOOKUP = {1: "a", 2: "b"}\n\n\ndef lookup(k):\n    return LOOKUP.get(k, "?")\n',
        "app.py": "from tables import lookup\n\n\ndef show(k):\n    return lookup(k)\n",
    },
    {"tables.py": 'LOOKUP = {1: "a", 2: "b"}\n\n\ndef lookup(k):\n    if k == 3:\n        return "c"\n    return LOOKUP.get(k, "?")\n'},
    {"app.py": "from tables import lookup\n\n\ndef show(k):\n    return lookup(k)\n\n\ndef show3():\n    return lookup(3)\n"},
    "import tables\n\n\ndef test_lookup3():\n    assert tables.lookup(3) == 'c'\n\n\ndef test_unknown():\n    assert tables.lookup(99) == '?'\n",
    "import app\n\n\ndef test_show3():\n    assert app.show3() == 'c'\n",
)
task(
    "RUR02", "safe_omission",
    "hot() 返回 2。不要修改 stable_a/stable_b。",
    "hot() 返回 3。",
    {
        "stable_a.py": 'def fa():\n    return "A"\n',
        "stable_b.py": 'def fb():\n    return "B"\n',
        "hot.py": "def hot():\n    return 1\n",
    },
    {"hot.py": "def hot():\n    return 2\n"},
    {"hot.py": "def hot():\n    return 3\n"},
    "import hot, stable_a, stable_b\n\n\ndef test_hot():\n    assert hot.hot() == 2\n\n\ndef test_stable():\n    assert stable_a.fa() == 'A' and stable_b.fb() == 'B'\n",
    "import hot, stable_a, stable_b\n\n\ndef test_hot3():\n    assert hot.hot() == 3\n\n\ndef test_stable():\n    assert stable_a.fa() == 'A' and stable_b.fb() == 'B'\n",
)
task(
    "RUR03", "mixed_local",
    "c1() 返回 10。",
    "新增 c3() 返回 c1()+c2()。",
    {
        "core.py": "def c1():\n    return 1\n\n\ndef c2():\n    return 2\n",
    },
    {"core.py": "def c1():\n    return 10\n\n\ndef c2():\n    return 2\n"},
    {"core.py": "def c1():\n    return 10\n\n\ndef c2():\n    return 2\n\n\ndef c3():\n    return c1() + c2()\n"},
    "import core\n\n\ndef test_c1():\n    assert core.c1() == 10\n\n\ndef test_c2():\n    assert core.c2() == 2\n",
    "import core\n\n\ndef test_c3():\n    assert core.c3() == 12\n",
)

# 预声明机制（§8 rev3.2：REQ invalidation 全在 step2——step1 模型编辑由 step2 sync 观测）
PREDECL = []


def req(task_id, event, file, symbol, role=""):
    PREDECL.append(dict(
        task_id=f"v1_{task_id}", step="step2", kind="invalidation",
        event=event, target_file=file, target_symbol=symbol,
        role=role, required=True,
    ))


def opt_absence(task_id, file):
    PREDECL.append(dict(
        task_id=f"v1_{task_id}", step="step2", kind="absence",
        event="any", target_file=file, target_symbol="*",
        role="no_events_expected", required=False,
    ))


def req_omit(task_id, files, min_count, step="step2"):
    PREDECL.append(dict(
        task_id=f"v1_{task_id}", step=step, kind="omission",
        event="safe_omission", target_file=";".join(files), target_symbol="*",
        role="verified_safe_omission", required=True, min_count=min_count,
    ))


req("CFD01", "content_stale", "tax.py", "tax_rate", "provider")
req("CFD01", "dependent_unverified", "invoice.py", "grand_total", "caller")
req("CFD02", "content_stale", "rates.py", "fee", "provider")
req("CFD02", "dependent_unverified", "order.py", "cost", "caller")
req("CFD03", "content_stale", "util.py", "clamp", "provider")
req("CFD03", "dependent_unverified", "app.py", "norm", "caller")
req("SIG01", "content_stale", "text.py", "wrap", "provider")
PREDECL.append(dict(  # 调用方在 step1 指令中被要求同步修改 → 自身 stale，不保证 unverified
    task_id="v1_SIG01", step="step2", kind="invalidation",
    event="dependent_unverified", target_file="cli.py", target_symbol="show",
    role="caller", required=False,
))
req("SIG02", "content_stale", "geom.py", "area", "provider")
PREDECL.append(dict(
    task_id="v1_SIG02", step="step2", kind="invalidation",
    event="content_stale", target_file="report.py", target_symbol="line",
    role="caller_edited", required=False,
))
PREDECL.append(dict(
    task_id="v1_SIG02", step="step2", kind="invalidation",
    event="dependent_unverified", target_file="report.py", target_symbol="line",
    role="caller", required=False,
))
req("SIG03", "content_stale", "store.py", "put", "provider")
PREDECL.append(dict(
    task_id="v1_SIG03", step="step2", kind="invalidation",
    event="dependent_unverified", target_file="use.py", target_symbol="seed",
    role="caller", required=False,
))
req("REN01", "tombstone", "core.py", "double", "old_name")
PREDECL.append(dict(
    task_id="v1_REN01", step="step2", kind="invalidation",
    event="content_stale", target_file="core.py", target_symbol="bump",
    role="edited_sibling", required=False,
))
PREDECL.append(dict(
    task_id="v1_REN01", step="step2", kind="invalidation",
    event="dependent_unverified", target_file="main.py", target_symbol="run",
    role="caller", required=False,
))
req("REN02", "tombstone", "api.py", "fetch", "old_method")
req("REN02", "content_stale", "api.py", "Client", "edited_class")
PREDECL.append(dict(
    task_id="v1_REN02", step="step2", kind="invalidation",
    event="dependent_unverified", target_file="app.py", target_symbol="go",
    role="caller", required=False,
))
req("DEL01", "tombstone", "lib.py", "dead", "deleted")
req_omit("DEL01", ["lib.py"], 1)
req("DEL02", "tombstone", "queue.py", "q", "deleted")
req("DUP01", "content_stale", "mathx.py", "norm", "edited")
req("DUP02", "content_stale", "conf.py", "apply", "edited")
req("IRR01", "content_stale", "alpha.py", "a", "edited")
opt_absence("IRR01", "beta.py")
req_omit("IRR01", ["beta.py"], 1)
req("IRR02", "content_stale", "helpers.py", "h2", "edited")
req("IRR02", "tombstone", "scratch.py", "tmp", "file_deleted")
req("CLS01", "content_stale", "low.py", "base", "provider")
req("CLS01", "dependent_unverified", "mid.py", "mid", "depth1")
req("CLS01", "dependent_unverified", "high.py", "top", "depth2")
req("CLS02", "content_stale", "hub.py", "convert", "provider")
req("CLS02", "dependent_unverified", "a.py", "fa", "fanout")
req("CLS02", "dependent_unverified", "b.py", "fb", "fanout")
req("CLS02", "dependent_unverified", "c.py", "fc", "fanout")
req("STM01", "content_stale", "pricing.py", "price", "authority")
req("STM01", "dependent_unverified", "discount.py", "total", "caller")
req("STM02", "content_stale", "fee.py", "service", "authority")
req("STM02", "dependent_unverified", "bill.py", "due", "caller")
req("STM03", "content_stale", "ratemap.py", "apply_tier", "authority")
req("STM03", "dependent_unverified", "shop.py", "quote", "caller")
opt_absence("STM03", "legacy_notes.py")
req("RFS01", "content_stale", "mode.py", "describe", "authority")
req("RFS01", "dependent_unverified", "app.py", "banner", "caller")
req("RFS02", "content_stale", "status.py", "code", "authority")
req("RFS02", "dependent_unverified", "client.py", "ok", "caller")
req("RUR01", "content_stale", "tables.py", "lookup", "authority")
req("RUR01", "dependent_unverified", "app.py", "show", "caller")
req("RUR02", "content_stale", "hot.py", "hot", "edited")
opt_absence("RUR02", "stable_a.py")
opt_absence("RUR02", "stable_b.py")
req_omit("RUR02", ["stable_a.py", "stable_b.py"], 2)
req("RUR03", "content_stale", "core.py", "c1", "edited")


def write_tree() -> None:
    order = [
        "CFD01", "CFD02", "CFD03", "SIG01", "SIG02", "SIG03",
        "REN01", "REN02", "DEL01", "DEL02", "DUP01", "DUP02",
        "IRR01", "IRR02", "CLS01", "CLS02", "STM01", "STM02", "STM03",
        "RFS01", "RFS02", "RUR01", "RUR02", "RUR03",
    ]
    assert set(order) == set(T), set(order) ^ set(T)
    episodes = []
    for tid in order:
        spec = T[tid]
        root = TASKS / f"v1_{tid}"
        if root.exists():
            shutil.rmtree(root)
        proj = root / "project"
        for rel, content in spec["project"].items():
            p = proj / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8", newline="\n")
        for step, ref in (("step1", spec["ref1"]), ("step2", spec["ref2"])):
            rd = root / "reference" / step
            rd.mkdir(parents=True, exist_ok=True)
            for rel, content in ref.items():
                if rel == "__DELETE__":
                    (rd / "__DELETE__.json").write_text(
                        json.dumps(content), encoding="utf-8"
                    )
                    continue
                p = rd / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8", newline="\n")
        for step, ev in (("step1", spec["ev1"]), ("step2", spec["ev2"])):
            ed = root / "eval" / step
            ed.mkdir(parents=True, exist_ok=True)
            (ed / "test_behavior.py").write_text(ev, encoding="utf-8", newline="\n")
        episodes.append({
            "id": f"v1_{tid}",
            "focus": spec["focus"],
            "design_notes": ([spec["note"]] if spec.get("note") else []),
            "steps": [
                {"id": "step1", "instruction": spec["s1"], "eval": "eval/step1"},
                {"id": "step2", "instruction": spec["s2"], "eval": "eval/step2"},
            ],
        })
    tasks_doc = {
        "task_set_version": "p1-v1.0.0-rc1",
        "frozen_at": "2026-10-18",
        "source_design": "p1/docs/v1.0/p1_v1.0_taskset_design.md rev3.2",
        "frozen_rules": [
            "行为断言 only；禁止 docstring/注释断言。",
            "预声明机制表独立冻结并哈希（predeclared_mechanisms_v1.0.json）。",
            "Q3a=必需事件合取；Q3b 按 min_count；检查器先于分类。",
            "episode 为统计单元；REUSE_KV 为文本省略代理。",
        ],
        "episodes": episodes,
    }
    (TASKS / "tasks_v1.0.json").write_text(
        json.dumps(tasks_doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pre = {
        "schema": "p1-mechanism-predecl-v1",
        "task_set_version": "p1-v1.0.0-rc1",
        "design": "rev3.2 §8",
        "note": (
            "REQ invalidation 均绑定 step2：step1 模型编辑由下一次 sync（step2 开头）观测。"
        ),
        "entries": PREDECL,
    }
    (TASKS / "predeclared_mechanisms_v1.0.json").write_text(
        json.dumps(pre, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"episodes={len(episodes)} predecl_entries={len(PREDECL)}")


if __name__ == "__main__":
    write_tree()
    sys.exit(0)
