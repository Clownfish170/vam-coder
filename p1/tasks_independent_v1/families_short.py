"""独立任务集 Short 族（Part2 independent-v1）：8 archetype × 2 变体 = 16 题，每题 2 步。

结构独立于 P1：症状修复 / 配置演化 / 重构搬迁 / 文档规格 / 异常契约 / 示例驱动 /
内部表示替换 / 编解码往返。变体间骨架不同（非纯换名）。
"""

from registry import T

# ============================================================ SF1 ind_short_bugfix
# 变体 a：median 偶数缺陷 + 空列表边界
_stats_a = (
    '"""Basic stats."""\n\n\n'
    "def median(xs):\n"
    "    xs = sorted(xs)\n"
    "    n = len(xs)\n"
    "    return xs[n // 2]\n\n\n"
    "def mean(xs):\n"
    "    return sum(xs) / len(xs) if xs else None\n"
)
_report_a = (
    '"""Reporting helpers."""\n\n\n'
    "from stats import mean\n\n\n"
    "def average_line(xs):\n"
    '    return f"avg={mean(xs)}"\n'
)
_m1_old = "    return xs[n // 2]\n"
_m1_new = (
    "    if n % 2 == 1:\n"
    "        return xs[n // 2]\n"
    "    return (xs[n // 2 - 1] + xs[n // 2]) / 2\n"
)
_m2_old = (
    "    if n % 2 == 1:\n"
    "        return xs[n // 2]\n"
)
_m2_new = (
    '    if n == 0:\n'
    '        raise ValueError("median of empty list")\n'
    "    if n % 2 == 1:\n"
    "        return xs[n // 2]\n"
)
T(
    id="ind_S01a",
    family="ind_short_bugfix",
    type="bugfix_diagnosis",
    difficulty="short",
    focus="症状式修复：median 偶数缺陷 → 空列表边界",
    files={"stats.py": _stats_a, "report.py": _report_a},
    steps=[
        {
            "instruction": (
                "请修改 stats.py 中的 median(xs)：它在偶数长度列表上结果错误"
                "（例如 [1, 2, 3, 4] 应得到 2.5）。"
            ),
            "tests": (
                "import stats\n\n\n"
                "def test_odd():\n"
                "    assert stats.median([3, 1, 2]) == 2\n\n\n"
                "def test_even():\n"
                "    assert stats.median([1, 2, 3, 4]) == 2.5\n\n\n"
                "def test_negative():\n"
                "    assert stats.median([-4, -2]) == -3\n"
            ),
            "ops": [("replace", "stats.py", _m1_old, _m1_new)],
            "expect_targets": {"stats.py"},
        },
        {
            "instruction": (
                "请修改 stats.py 中的 median(xs)：空列表应抛出 ValueError"
                "（当前抛出的是 IndexError）。"
            ),
            "tests": (
                "import pytest\n\n"
                "import stats\n\n\n"
                "def test_empty():\n"
                "    with pytest.raises(ValueError):\n"
                "        stats.median([])\n\n\n"
                "def test_even_regression():\n"
                "    assert stats.median([1, 2, 3, 4]) == 2.5\n\n\n"
                "def test_odd_regression():\n"
                "    assert stats.median([3, 1, 2]) == 2\n"
            ),
            "ops": [("replace", "stats.py", _m2_old, _m2_new)],
            "expect_targets": {"stats.py"},
        },
    ],
    info_points=[
        {"id": "ip_median_even", "type": "implementation",
         "value": "中位取两中间值平均",
         "locator": "instruction:step1 + stats.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_median_regression", "type": "history",
         "value": "median([1,2,3,4])==2.5",
         "locator": "workspace stats.py (step1 修复) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：百分数折扣缺陷 + 边界钳制
_tax_b = (
    '"""Pricing."""\n\n\n'
    "def apply_discount(price, pct):\n"
    "    return price - price * pct\n"
)
_p1_old = "    return price - price * pct\n"
_p1_new = "    return price - price * (pct / 100.0)\n"
_p2_old = "    return price - price * (pct / 100.0)\n"
_p2_new = (
    "    if pct < 0:\n"
    "        pct = 0\n"
    "    if pct > 100:\n"
    "        pct = 100\n"
    "    return price - price * (pct / 100.0)\n"
)
T(
    id="ind_S01b",
    family="ind_short_bugfix",
    type="bugfix_diagnosis",
    difficulty="short",
    focus="症状式修复：百分数语义缺陷 → 钳制边界",
    files={"tax.py": _tax_b},
    steps=[
        {
            "instruction": (
                "请修改 tax.py 中的 apply_discount(price, pct)：pct 是百分数语义"
                "（10 表示 10%），当前结果明显偏离预期。"
            ),
            "tests": (
                "import tax\n\n\n"
                "def test_ten_percent():\n"
                "    assert tax.apply_discount(100, 10) == 90.0\n\n\n"
                "def test_zero():\n"
                "    assert tax.apply_discount(80, 0) == 80\n\n\n"
                "def test_half():\n"
                "    assert tax.apply_discount(200, 50) == 100.0\n"
            ),
            "ops": [("replace", "tax.py", _p1_old, _p1_new)],
            "expect_targets": {"tax.py"},
        },
        {
            "instruction": (
                "tax.py 中的 apply_discount(price, pct)：pct 为 0 时应原样返回 price；"
                "pct 超过 100 时按 100 处理（当前未做边界处理）。"
            ),
            "tests": (
                "import tax\n\n\n"
                "def test_zero_identity():\n"
                "    assert tax.apply_discount(80, 0) == 80\n\n\n"
                "def test_clamp_over():\n"
                "    assert tax.apply_discount(100, 150) == 0\n\n\n"
                "def test_negative_clamp():\n"
                "    assert tax.apply_discount(100, -5) == 100\n\n\n"
                "def test_regression():\n"
                "    assert tax.apply_discount(100, 10) == 90.0\n"
            ),
            "ops": [("replace", "tax.py", _p2_old, _p2_new)],
            "expect_targets": {"tax.py"},
        },
    ],
    info_points=[
        {"id": "ip_pct_semantics", "type": "implementation",
         "value": "price * (pct / 100.0)",
         "locator": "instruction:step1 + tax.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_discount_regression", "type": "history",
         "value": "apply_discount(100,10)==90.0",
         "locator": "workspace tax.py (step1 修复) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ SF2 ind_short_config
# 变体 a：JSON 超时配置 + DEFAULTS 同步
_cfg_a = '{\n  "retries": 3,\n  "timeout_s": 30\n}\n'
_loader_a = (
    '"""Config loading."""\n\n\n'
    "import json\n"
    "from pathlib import Path\n\n\n"
    'DEFAULTS = {"retries": 1, "timeout_s": 10}\n\n\n'
    'def load(path="app_config.json"):\n'
    "    base = Path(__file__).resolve().parent\n"
    "    target = Path(path)\n"
    "    if not target.is_absolute():\n"
    "        target = base / target\n"
    "    data = json.loads(target.read_text(encoding=\"utf-8\"))\n"
    "    out = dict(DEFAULTS)\n"
    "    out.update(data)\n"
    "    return out\n"
)
_app_a = (
    '"""Tiny app."""\n\n\n'
    "from config import load\n\n\n"
    "def describe():\n"
    "    cfg = load()\n"
    '    return f"retries={cfg[\'retries\']}"\n'
)
T(
    id="ind_S02a",
    family="ind_short_config",
    type="config_evolution",
    difficulty="short",
    focus="JSON 配置值变更 + 读取器默认值同步",
    files={"app_config.json": _cfg_a, "config.py": _loader_a, "app.py": _app_a},
    steps=[
        {
            "instruction": "app_config.json 中 timeout_s 应为 60（当前为 30）。",
            "tests": (
                "import config\n\n\n"
                "def test_timeout():\n"
                '    assert config.load()["timeout_s"] == 60\n\n\n'
                "def test_retries_unchanged():\n"
                '    assert config.load()["retries"] == 3\n\n\n'
                "def test_describe():\n"
                "    import app\n"
                '    assert "retries=3" in app.describe()\n'
            ),
            "ops": [("replace", "app_config.json", '"timeout_s": 30', '"timeout_s": 60')],
            "expect_targets": {"app_config.json"},
        },
        {
            "instruction": (
                "config.py 的 DEFAULTS 中 timeout_s 应为 45（当前为 10），"
                "使配置文件缺失该键时取 45。"
            ),
            "tests": (
                "import json\n"
                "import tempfile\n\n"
                "import config\n\n\n"
                "def test_defaults():\n"
                '    assert config.DEFAULTS["timeout_s"] == 45\n\n\n'
                "def test_missing_key_fallback(tmp_path):\n"
                '    p = tmp_path / "c.json"\n'
                '    p.write_text(json.dumps({"retries": 2}), encoding="utf-8")\n'
                '    assert config.load(str(p))["timeout_s"] == 45\n\n\n'
                "def test_file_still_wins():\n"
                '    assert config.load()["timeout_s"] == 60\n'
            ),
            "ops": [("replace", "config.py",
                     'DEFAULTS = {"retries": 1, "timeout_s": 10}',
                     'DEFAULTS = {"retries": 1, "timeout_s": 45}')],
            "expect_targets": {"config.py"},
        },
    ],
    info_points=[
        {"id": "ip_timeout_cfg", "type": "critical_data",
         "value": "60",
         "locator": "instruction:step1 + app_config.json",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_file_wins", "type": "history",
         "value": "load() 主配置 timeout_s==60（step1 值仍然生效）",
         "locator": "app_config.json (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
        {"id": "ip_defaults_timeout", "type": "critical_data",
         "value": "45",
         "locator": "instruction:step2 + config.py",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
    ],
)

# 变体 b：端口变更 + 新增 workers 字段贯穿 loader 与 app
_srv_b = '{\n  "host": "127.0.0.1",\n  "port": 8080\n}\n'
_loader_b = (
    '"""Server config."""\n\n\n'
    "import json\n"
    "from pathlib import Path\n\n\n"
    'DEFAULTS = {"host": "0.0.0.0", "port": 80, "workers": 1}\n\n\n'
    'def load(path="server.json"):\n'
    "    base = Path(__file__).resolve().parent\n"
    "    target = Path(path)\n"
    "    if not target.is_absolute():\n"
    "        target = base / target\n"
    "    data = json.loads(target.read_text(encoding=\"utf-8\"))\n"
    "    out = dict(DEFAULTS)\n"
    "    out.update(data)\n"
    "    return out\n"
)
_srv_app_b = (
    '"""Server describe."""\n\n\n'
    "from config import load\n\n\n"
    "def banner():\n"
    "    cfg = load()\n"
    '    return f"{cfg[\'host\']}:{cfg[\'port\']}"\n'
)
T(
    id="ind_S02b",
    family="ind_short_config",
    type="config_evolution",
    difficulty="short",
    focus="JSON 端口变更 + 新字段接入 banner",
    files={"server.json": _srv_b, "config.py": _loader_b, "app.py": _srv_app_b},
    steps=[
        {
            "instruction": "server.json 中 port 应为 9000（当前为 8080）。",
            "tests": (
                "import config\n\n\n"
                "def test_port():\n"
                '    assert config.load()["port"] == 9000\n\n\n'
                "def test_host_unchanged():\n"
                '    assert config.load()["host"] == "127.0.0.1"\n\n\n'
                "def test_banner():\n"
                "    import app\n"
                '    assert app.banner() == "127.0.0.1:9000"\n'
            ),
            "ops": [("replace", "server.json", '"port": 8080', '"port": 9000')],
            "expect_targets": {"server.json"},
        },
        {
            "instruction": (
                "server.json 新增 workers 字段，值为 4；并同步修改 app.py 的 banner，"
                "输出格式变为 host:port x workers（例如 127.0.0.1:9000 x 4）。"
            ),
            "tests": (
                "import config\n\n\n"
                "def test_workers_in_file():\n"
                '    assert config.load()["workers"] == 4\n\n\n'
                "def test_banner_format():\n"
                "    import app\n"
                '    assert app.banner() == "127.0.0.1:9000 x 4"\n\n\n'
                "def test_port_regression():\n"
                '    assert config.load()["port"] == 9000\n'
            ),
            "ops": [
                ("replace", "server.json", '"port": 9000\n}',
                 '"port": 9000,\n  "workers": 4\n}'),
                ("replace", "app.py",
                 '    return f"{cfg[\'host\']}:{cfg[\'port\']}"',
                 '    return f"{cfg[\'host\']}:{cfg[\'port\']} x {cfg[\'workers\']}"'),
            ],
            "expect_targets": {"server.json", "app.py"},
        },
    ],
    info_points=[
        {"id": "ip_port_cfg", "type": "critical_data",
         "value": "9000",
         "locator": "instruction:step1 + server.json",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_banner_contract", "type": "interface",
         "value": "host:port x workers",
         "locator": "instruction:step2 + app.py",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
        {"id": "ip_port_regression", "type": "history",
         "value": "port==9000（step1 值在 step2 后仍生效）",
         "locator": "server.json (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ SF3 ind_short_refactor
# 变体 a：跨文件重命名
_eng_a = (
    '"""Engine."""\n\n\n'
    "def compute(x):\n"
    "    return x * 2 + 1\n\n\n"
    "def helper(x):\n"
    "    return compute(x) - 1\n"
)
_cli_a = (
    '"""CLI."""\n\n\n'
    "from engine import compute\n\n\n"
    "def run(x):\n"
    "    return compute(x)\n"
)
T(
    id="ind_S03a",
    family="ind_short_refactor",
    type="cross_file_rename",
    difficulty="short",
    focus="compute→evaluate 跨文件重命名 + 新增调用方",
    files={"engine.py": _eng_a, "cli.py": _cli_a},
    steps=[
        {
            "instruction": (
                "将 engine.py 中的 compute 重命名为 evaluate，"
                "并同步修改 cli.py 中的引用。"
            ),
            "tests": (
                "import engine\n"
                "import cli\n\n\n"
                "def test_new_name():\n"
                "    assert engine.evaluate(3) == 7\n\n\n"
                "def test_old_gone():\n"
                "    assert not hasattr(engine, \"compute\")\n"
                "    assert not hasattr(cli, \"compute\")\n\n\n"
                "def test_caller():\n"
                "    assert cli.run(3) == 7\n\n\n"
                "def test_helper():\n"
                "    assert engine.helper(3) == 6\n"
            ),
            "ops": [
                ("replace", "engine.py", "def compute(x):", "def evaluate(x):"),
                ("replace", "engine.py", "    return compute(x) - 1",
                 "    return evaluate(x) - 1"),
                ("replace", "cli.py", "from engine import compute",
                 "from engine import evaluate"),
                ("replace", "cli.py", "    return compute(x)",
                 "    return evaluate(x)"),
            ],
            "expect_targets": {"engine.py", "cli.py"},
        },
        {
            "instruction": "cli.py 新增 double_run(x)：返回 run(x) + run(x + 1)。",
            "tests": (
                "import engine\n"
                "import cli\n\n\n"
                "def test_double_run():\n"
                "    assert cli.double_run(2) == cli.run(2) + cli.run(3)\n"
                "    assert cli.double_run(2) == 12\n\n\n"
                "def test_rename_regression():\n"
                "    assert not hasattr(engine, \"compute\")\n"
                "    assert engine.evaluate(3) == 7\n\n\n"
                "def test_run_regression():\n"
                "    assert cli.run(3) == 7\n"
            ),
            "ops": [
                ("replace", "cli.py",
                 "def run(x):\n    return evaluate(x)\n",
                 "def run(x):\n    return evaluate(x)\n\n\n"
                 "def double_run(x):\n    return run(x) + run(x + 1)\n"),
            ],
            "expect_targets": {"cli.py"},
        },
    ],
    info_points=[
        {"id": "ip_rename_target", "type": "interface",
         "value": "evaluate（compute 不复存在）",
         "locator": "instruction:step1 + engine.py/cli.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_rename_regression", "type": "history",
         "value": "engine.compute 已移除且 evaluate(3)==7",
         "locator": "workspace (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：函数搬迁（util → text）
_util_b = (
    '"""Utilities."""\n\n\n'
    "def slugify(s):\n"
    "    return s.lower().replace(\" \", \"-\")\n\n\n"
    "def shout(s):\n"
    "    return s.upper()\n"
)
_text_b = (
    '"""Text helpers."""\n\n\n'
    "def wrap(s, n):\n"
    "    return s[:n]\n"
)
_web_b = (
    '"""Web glue."""\n\n\n'
    "from util import slugify\n\n\n"
    "def page_title(s):\n"
    '    return slugify(s) + ".html"\n'
)
T(
    id="ind_S03b",
    family="ind_short_refactor",
    type="cross_file_move",
    difficulty="short",
    focus="slugify 从 util 搬迁到 text + 调用方同步",
    files={"util.py": _util_b, "text.py": _text_b, "web.py": _web_b},
    steps=[
        {
            "instruction": (
                "把 util.py 中的 slugify 搬迁到 text.py，"
                "并同步修改 web.py 中的引用；util.py 不再保留该函数。"
            ),
            "tests": (
                "import util\n"
                "import text\n"
                "import web\n\n\n"
                "def test_moved():\n"
                "    assert text.slugify(\"Hello World\") == \"hello-world\"\n\n\n"
                "def test_removed_from_util():\n"
                "    assert not hasattr(util, \"slugify\")\n\n\n"
                "def test_caller():\n"
                '    assert web.page_title("Hello World") == "hello-world.html"\n\n\n'
                "def test_util_still_has_shout():\n"
                '    assert util.shout("ab") == "AB"\n'
            ),
            "ops": [
                ("replace", "util.py",
                 'def slugify(s):\n    return s.lower().replace(" ", "-")\n\n\n',
                 ""),
                ("replace", "text.py",
                 'def wrap(s, n):\n    return s[:n]\n',
                 'def wrap(s, n):\n    return s[:n]\n\n\n'
                 'def slugify(s):\n    return s.lower().replace(" ", "-")\n'),
                ("replace", "web.py", "from util import slugify",
                 "from text import slugify"),
            ],
            "expect_targets": {"util.py", "text.py", "web.py"},
        },
        {
            "instruction": "text.py 新增 slug_list(items)：对每个元素调用 slugify 并返回列表。",
            "tests": (
                "import text\n"
                "import util\n\n\n"
                "def test_slug_list():\n"
                '    assert text.slug_list(["A B", "c d"]) == ["a-b", "c-d"]\n\n\n'
                "def test_move_regression():\n"
                '    assert text.slugify("X Y") == "x-y"\n'
                "    assert not hasattr(util, \"slugify\")\n\n\n"
                "def test_wrap_regression():\n"
                '    assert text.wrap("abcdef", 3) == "abc"\n'
            ),
            "ops": [
                ("replace", "text.py",
                 'def slugify(s):\n    return s.lower().replace(" ", "-")\n',
                 'def slugify(s):\n    return s.lower().replace(" ", "-")\n\n\n'
                 "def slug_list(items):\n"
                 "    return [slugify(x) for x in items]\n"),
            ],
            "expect_targets": {"text.py"},
        },
    ],
    info_points=[
        {"id": "ip_move_target", "type": "interface",
         "value": "slugify 归属 text.py（util.py 已移除）",
         "locator": "instruction:step1 + util.py/text.py/web.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_move_regression", "type": "history",
         "value": "util.slugify 不存在且 text.slugify 可用",
         "locator": "workspace (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ SF4 ind_short_specdoc
# 变体 a：README 承载 gcd 规格
_ratio_a = (
    '"""Fraction helpers."""\n\n\n'
    "def simplify(a, b):\n"
    "    return a, b\n"
)
_readme_a = (
    "# ratio.py spec\n\n"
    "simplify(a, b) must return the reduced fraction as a tuple:\n"
    "- divide both sides by their greatest common divisor (gcd)\n"
    "- gcd(0, 0) is undefined: return (0, 1)\n"
    "- keep the sign on the numerator\n"
)
T(
    id="ind_S04a",
    family="ind_short_specdoc",
    type="spec_from_docs",
    difficulty="short",
    focus="规格在 README：按文档实现 gcd 约分",
    files={"README.md": _readme_a, "ratio.py": _ratio_a},
    steps=[
        {
            "instruction": "请按 README.md 中 ratio.py 的规格实现 ratio.py 的 simplify(a, b)。",
            "tests": (
                "import ratio\n\n\n"
                "def test_basic():\n"
                "    assert ratio.simplify(4, 6) == (2, 3)\n\n\n"
                "def test_sign():\n"
                "    assert ratio.simplify(-4, 6) == (-2, 3)\n\n\n"
                "def test_zero_zero():\n"
                "    assert ratio.simplify(0, 0) == (0, 1)\n\n\n"
                "def test_already_reduced():\n"
                "    assert ratio.simplify(3, 5) == (3, 5)\n"
            ),
            "ops": [
                ("replace", "ratio.py",
                 "def simplify(a, b):\n    return a, b\n",
                 "def simplify(a, b):\n"
                 "    if a == 0 and b == 0:\n"
                 "        return (0, 1)\n"
                 "    g = _gcd(abs(a), abs(b))\n"
                 "    na, nb = a // g, b // g\n"
                 "    if nb < 0:\n"
                 "        na, nb = -na, -nb\n"
                 "    return (na, nb)\n\n\n"
                 "def _gcd(x, y):\n"
                 "    while y:\n"
                 "        x, y = y, x % y\n"
                 "    return x or 1\n"),
            ],
            "expect_targets": {"README.md", "ratio.py"},
        },
        {
            "instruction": (
                "README.md 规格修订了 b == 0 的规则（含 a == 0 的情形），"
                "请同步实现到 ratio.py 的 simplify(a, b)。"
            ),
            "tests": (
                "import pytest\n\n"
                "import ratio\n\n\n"
                "def test_b_zero():\n"
                "    with pytest.raises(ValueError):\n"
                "        ratio.simplify(5, 0)\n\n\n"
                "def test_zero_zero():\n"
                "    with pytest.raises(ValueError):\n"
                "        ratio.simplify(0, 0)\n\n\n"
                "def test_basic_regression():\n"
                "    assert ratio.simplify(4, 6) == (2, 3)\n\n\n"
                "def test_negative_regression():\n"
                "    assert ratio.simplify(-4, 6) == (-2, 3)\n"
            ),
            "ops": [
                ("replace", "README.md",
                 "- gcd(0, 0) is undefined: return (0, 1)\n",
                 "- if b == 0 (any a, including 0): raise ValueError\n"),
                ("replace", "ratio.py",
                 "def simplify(a, b):\n"
                 "    if a == 0 and b == 0:\n"
                 "        return (0, 1)\n",
                 "def simplify(a, b):\n"
                 "    if b == 0:\n"
                 '        raise ValueError("b is zero")\n'),
            ],
            "expect_targets": {"README.md", "ratio.py"},
        },
    ],
    info_points=[
        {"id": "ip_gcd_spec", "type": "implementation",
         "value": "按 gcd 约分，符号在分子，(0,0)→(0,1)",
         "locator": "README.md（不在指令）",
         "needed_by_steps": [1],
         "redundant_in_instruction": False},
        {"id": "ip_ratio_target", "type": "implementation",
         "value": "ratio.py::simplify",
         "locator": "instruction:step1",
         "needed_by_steps": [1],
         "redundant_in_instruction": True},
        {"id": "ip_b0_rule", "type": "implementation",
         "value": "b==0 → ValueError（step2 规则修订，取代 (0,1) 旧规）",
         "locator": "README.md 修订段（指令不复述实现细节）",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
        {"id": "ip_simplify_regression", "type": "history",
         "value": "simplify(4,6)==(2,3) 且 simplify(-4,6)==(-2,3)（step1 行为保持）",
         "locator": "ratio.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：README 承载 round-half-up 规格
_round_b = (
    '"""Rounding."""\n\n\n'
    "def round1(x):\n"
    "    return round(x, 1)\n"
)
_readme_b = (
    "# round1 spec\n\n"
    "round1(x) rounds to 1 decimal place using HALF-UP on the decimal "
    "digit (not banker's rounding):\n"
    "- 2.25 -> 2.3\n"
    "- 2.35 -> 2.4\n"
    "- -2.25 -> -2.3 (magnitude grows away from zero on .5)\n"
)
T(
    id="ind_S04b",
    family="ind_short_specdoc",
    type="spec_from_docs",
    difficulty="short",
    focus="规格在 README：HALF-UP 舍入（对抗内建 banker's rounding），再扩展两位小数",
    files={"README.md": _readme_b, "rounding.py": _round_b},
    steps=[
        {
            "instruction": "请按 README.md 中 round1 的规格实现 rounding.py 的 round1(x)。",
            "tests": (
                "import rounding\n\n\n"
                "def test_half_up():\n"
                "    assert rounding.round1(2.25) == 2.3\n\n\n"
                "def test_half_up_2():\n"
                "    assert rounding.round1(2.35) == 2.4\n\n\n"
                "def test_negative():\n"
                "    assert rounding.round1(-2.25) == -2.3\n\n\n"
                "def test_plain():\n"
                "    assert rounding.round1(2.4) == 2.4\n"
            ),
            "ops": [
                ("replace", "rounding.py",
                 "def round1(x):\n    return round(x, 1)\n",
                 "def round1(x):\n"
                 "    from decimal import ROUND_HALF_UP, Decimal\n"
                 "    return float(\n"
                 "        Decimal(str(x)).quantize(Decimal(\"0.1\"), rounding=ROUND_HALF_UP)\n"
                 "    )\n"),
            ],
            "expect_targets": {"README.md", "rounding.py"},
        },
        {
            "instruction": (
                "README.md 规格新增了 round2(x)（保留两位小数，同一 HALF-UP 规则），"
                "请同步实现到 rounding.py。"
            ),
            "tests": (
                "import rounding\n\n\n"
                "def test_round2():\n"
                "    assert rounding.round2(2.225) == 2.23\n\n\n"
                "def test_round2_plain():\n"
                "    assert rounding.round2(1.5) == 1.5\n\n\n"
                "def test_round1_regression():\n"
                "    assert rounding.round1(2.25) == 2.3\n"
                "    assert rounding.round1(-2.25) == -2.3\n"
            ),
            "ops": [
                ("replace", "README.md",
                 "- -2.25 -> -2.3 (magnitude grows away from zero on .5)\n",
                 "- -2.25 -> -2.3 (magnitude grows away from zero on .5)\n"
                 "\n"
                 "round2(x) rounds to 2 decimal places with the same HALF-UP rule:\n"
                 "- 2.225 -> 2.23\n"
                 "- 1.5 -> 1.5\n"),
                ("replace", "rounding.py",
                 "def round1(x):\n"
                 "    from decimal import ROUND_HALF_UP, Decimal\n"
                 "    return float(\n"
                 "        Decimal(str(x)).quantize(Decimal(\"0.1\"), rounding=ROUND_HALF_UP)\n"
                 "    )\n",
                 "def round1(x):\n"
                 "    from decimal import ROUND_HALF_UP, Decimal\n"
                 "    return float(\n"
                 "        Decimal(str(x)).quantize(Decimal(\"0.1\"), rounding=ROUND_HALF_UP)\n"
                 "    )\n\n\n"
                 "def round2(x):\n"
                 "    from decimal import ROUND_HALF_UP, Decimal\n"
                 "    return float(\n"
                 "        Decimal(str(x)).quantize(Decimal(\"0.01\"), rounding=ROUND_HALF_UP)\n"
                 "    )\n"),
            ],
            "expect_targets": {"README.md", "rounding.py"},
        },
    ],
    info_points=[
        {"id": "ip_half_up_spec", "type": "implementation",
         "value": "HALF-UP（2.25→2.3，-2.25→-2.3）",
         "locator": "README.md（不在指令）",
         "needed_by_steps": [1],
         "redundant_in_instruction": False},
        {"id": "ip_round_target", "type": "implementation",
         "value": "rounding.py::round1",
         "locator": "instruction:step1",
         "needed_by_steps": [1],
         "redundant_in_instruction": True},
        {"id": "ip_round2_spec", "type": "implementation",
         "value": "round2 两位小数 HALF-UP",
         "locator": "README.md 新增段 + instruction:step2",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
        {"id": "ip_halfup_regression", "type": "history",
         "value": "round1(2.25)==2.3 且 round1(-2.25)==-2.3（step1 行为保持）",
         "locator": "rounding.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ SF5 ind_short_excep
# 变体 a：提现异常契约
_bal_a = (
    '"""Balances."""\n\n\n'
    "def withdraw(balance, amount):\n"
    "    return balance - amount\n"
)
_readme_ba = (
    "# withdraw contract\n\n"
    "withdraw(balance, amount) must:\n"
    "- raise ValueError when amount <= 0\n"
    "- raise InsufficientFunds (defined in balance.py) when amount > balance\n"
    "- otherwise return the new balance\n"
)
T(
    id="ind_S05a",
    family="ind_short_excep",
    type="exception_contract",
    difficulty="short",
    focus="按 README 契约分两步实现 withdraw 异常体系",
    files={"README.md": _readme_ba, "balance.py": _bal_a},
    steps=[
        {
            "instruction": (
                "按 README.md 中 withdraw 的契约，修改 balance.py 的 withdraw："
                "amount <= 0 时抛 ValueError。"
            ),
            "tests": (
                "import pytest\n\n"
                "import balance\n\n\n"
                "def test_amount_nonpositive():\n"
                "    with pytest.raises(ValueError):\n"
                "        balance.withdraw(100, 0)\n"
                "    with pytest.raises(ValueError):\n"
                "        balance.withdraw(100, -5)\n\n\n"
                "def test_ok():\n"
                "    assert balance.withdraw(100, 30) == 70\n"
            ),
            "ops": [
                ("replace", "balance.py",
                 "def withdraw(balance, amount):\n    return balance - amount\n",
                 "def withdraw(balance, amount):\n"
                 "    if amount <= 0:\n"
                 '        raise ValueError("amount")\n'
                 "    return balance - amount\n"),
            ],
            "expect_targets": {"README.md", "balance.py"},
        },
        {
            "instruction": (
                "README.md 中 withdraw 契约的第二条（余额不足）也需实现到 balance.py。"
            ),
            "tests": (
                "import pytest\n\n"
                "import balance\n\n\n"
                "def test_insufficient():\n"
                "    with pytest.raises(balance.InsufficientFunds):\n"
                "        balance.withdraw(50, 80)\n\n\n"
                "def test_amount_regression():\n"
                "    with pytest.raises(ValueError):\n"
                "        balance.withdraw(100, 0)\n\n\n"
                "def test_ok_regression():\n"
                "    assert balance.withdraw(100, 30) == 70\n"
            ),
            "ops": [
                ("replace", "balance.py",
                 'def withdraw(balance, amount):\n'
                 '    if amount <= 0:\n'
                 '        raise ValueError("amount")\n'
                 '    return balance - amount\n',
                 'class InsufficientFunds(Exception):\n'
                 '    pass\n\n\n'
                 'def withdraw(balance, amount):\n'
                 '    if amount <= 0:\n'
                 '        raise ValueError("amount")\n'
                 '    if amount > balance:\n'
                 '        raise InsufficientFunds("balance")\n'
                 '    return balance - amount\n'),
            ],
            "expect_targets": {"README.md", "balance.py"},
        },
    ],
    info_points=[
        {"id": "ip_amount_rule", "type": "implementation",
         "value": "amount<=0 → ValueError",
         "locator": "README.md + instruction:step1",
         "needed_by_steps": [1],
         "redundant_in_instruction": True},
        {"id": "ip_insufficient_class", "type": "interface",
         "value": "InsufficientFunds（类名只在 README）",
         "locator": "README.md（指令仅称'第二条'）",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
        {"id": "ip_amount_regression", "type": "history",
         "value": "amount<=0 → ValueError（step1 行为保持）",
         "locator": "balance.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：Feed 行解析异常契约
_feed_b = (
    '"""Feed parsing."""\n\n\n'
    "def parse_line(line):\n"
    "    parts = line.split(\",\")\n"
    "    return parts[0], parts[1]\n"
)
_readme_fb = (
    "# parse_line contract\n\n"
    "parse_line(line) splits one `key,value` record:\n"
    "- must raise BadFeed (defined in feed.py) when the line has "
    "fewer than 2 comma-separated fields\n"
    "- must raise BadFeed when either field is empty/whitespace\n"
    "- otherwise return (key, value) with surrounding spaces stripped\n"
)
T(
    id="ind_S05b",
    family="ind_short_excep",
    type="exception_contract",
    difficulty="short",
    focus="按 README 契约分两步实现 BadFeed 校验",
    files={"README.md": _readme_fb, "feed.py": _feed_b},
    steps=[
        {
            "instruction": (
                "按 README.md 中 parse_line 的契约，修改 feed.py 的 parse_line："
                "字段不足 2 个时抛 BadFeed（异常类定义在 feed.py）。"
            ),
            "tests": (
                "import pytest\n\n"
                "import feed\n\n\n"
                "def test_too_few():\n"
                "    with pytest.raises(feed.BadFeed):\n"
                "        feed.parse_line(\"lonely\")\n\n\n"
                "def test_ok():\n"
                '    assert feed.parse_line("a,b") == ("a", "b")\n'
            ),
            "ops": [
                ("replace", "feed.py",
                 'def parse_line(line):\n'
                 '    parts = line.split(",")\n'
                 '    return parts[0], parts[1]\n',
                 'class BadFeed(Exception):\n'
                 '    pass\n\n\n'
                 'def parse_line(line):\n'
                 '    parts = line.split(",")\n'
                 '    if len(parts) < 2:\n'
                 '        raise BadFeed("fields")\n'
                 '    return parts[0], parts[1]\n'),
            ],
            "expect_targets": {"README.md", "feed.py"},
        },
        {
            "instruction": (
                "README.md 中 parse_line 契约的空字段规则也需实现到 feed.py："
                "任一字段为空白时抛 BadFeed；非空时返回去除首尾空格的元组。"
            ),
            "tests": (
                "import pytest\n\n"
                "import feed\n\n\n"
                "def test_empty_field():\n"
                "    with pytest.raises(feed.BadFeed):\n"
                '        feed.parse_line("a,")\n'
                "    with pytest.raises(feed.BadFeed):\n"
                '        feed.parse_line(" ,b")\n\n\n'
                "def test_strip():\n"
                '    assert feed.parse_line("  a , b  ") == ("a", "b")\n\n\n'
                "def test_few_fields_regression():\n"
                "    with pytest.raises(feed.BadFeed):\n"
                '        feed.parse_line("lonely")\n'
            ),
            "ops": [
                ("replace", "feed.py",
                 'def parse_line(line):\n'
                 '    parts = line.split(",")\n'
                 '    if len(parts) < 2:\n'
                 '        raise BadFeed("fields")\n'
                 '    return parts[0], parts[1]\n',
                 'def parse_line(line):\n'
                 '    parts = line.split(",")\n'
                 '    if len(parts) < 2:\n'
                 '        raise BadFeed("fields")\n'
                 '    key, value = parts[0].strip(), parts[1].strip()\n'
                 '    if not key or not value:\n'
                 '        raise BadFeed("empty")\n'
                 '    return key, value\n'),
            ],
            "expect_targets": {"README.md", "feed.py"},
        },
    ],
    info_points=[
        {"id": "ip_badfeed_class", "type": "interface",
         "value": "BadFeed（类名与抛出时机在 README）",
         "locator": "README.md + instruction:step1",
         "needed_by_steps": [1],
         "redundant_in_instruction": True},
        {"id": "ip_empty_rule", "type": "implementation",
         "value": "空字段 → BadFeed；非空 strip 后返回",
         "locator": "README.md（指令不复述实现细节）",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
        {"id": "ip_fields_regression", "type": "history",
         "value": "字段不足 → BadFeed（step1 行为保持）",
         "locator": "feed.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ SF6 ind_short_examples
# 变体 a：pad_left / pad_right 示例驱动
_pad_a = (
    '"""Padding."""\n\n\n'
    "def pad_left(s, n, ch):\n"
    "    return s\n"
)
T(
    id="ind_S06a",
    family="ind_short_examples",
    type="example_driven",
    difficulty="short",
    focus="示例驱动实现 pad_left，再对称扩展 pad_right",
    files={"expand.py": _pad_a},
    steps=[
        {
            "instruction": (
                "实现 expand.py 的 pad_left(s, n, ch)：s 长度不足 n 时左侧用 ch 补足到长度 n。"
                "示例：pad_left('7', 3, '0') == '007'；"
                "pad_left('hi', 5, '.') == '...hi'；"
                "pad_left('hello', 3, '0') == 'hello'。"
            ),
            "tests": (
                "import expand\n\n\n"
                "def test_pad():\n"
                '    assert expand.pad_left("7", 3, "0") == "007"\n\n\n'
                "def test_pad_dots():\n"
                '    assert expand.pad_left("hi", 5, ".") == "...hi"\n\n\n'
                "def test_no_pad_needed():\n"
                '    assert expand.pad_left("hello", 3, "0") == "hello"\n'
            ),
            "ops": [
                ("replace", "expand.py",
                 "def pad_left(s, n, ch):\n    return s\n",
                 "def pad_left(s, n, ch):\n"
                 "    if len(s) >= n:\n"
                 "        return s\n"
                 "    return ch * (n - len(s)) + s\n"),
            ],
            "expect_targets": {"expand.py"},
        },
        {
            "instruction": (
                "expand.py 新增 pad_right(s, n, ch)：右侧补足，规则与 pad_left 对称。"
                "示例：pad_right('7', 3, '0') == '700'；"
                "pad_right('hi', 5, '.') == 'hi...'。"
            ),
            "tests": (
                "import expand\n\n\n"
                "def test_pad_right():\n"
                '    assert expand.pad_right("7", 3, "0") == "700"\n\n\n'
                "def test_pad_right_dots():\n"
                '    assert expand.pad_right("hi", 5, ".") == "hi..."\n\n\n'
                "def test_pad_left_regression():\n"
                '    assert expand.pad_left("7", 3, "0") == "007"\n'
            ),
            "ops": [
                ("replace", "expand.py",
                 "def pad_left(s, n, ch):\n"
                 "    if len(s) >= n:\n"
                 "        return s\n"
                 "    return ch * (n - len(s)) + s\n",
                 "def pad_left(s, n, ch):\n"
                 "    if len(s) >= n:\n"
                 "        return s\n"
                 "    return ch * (n - len(s)) + s\n\n\n"
                 "def pad_right(s, n, ch):\n"
                 "    if len(s) >= n:\n"
                 "        return s\n"
                 "    return s + ch * (n - len(s))\n"),
            ],
            "expect_targets": {"expand.py"},
        },
    ],
    info_points=[
        {"id": "ip_pad_left_rule", "type": "implementation",
         "value": "左侧补足到长度 n（示例归纳）",
         "locator": "instruction:step1 示例",
         "needed_by_steps": [1],
         "redundant_in_instruction": True},
        {"id": "ip_pad_symmetry", "type": "interface",
         "value": "pad_right 与 pad_left 对称",
         "locator": "instruction:step2 + pad_left 先例",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
        {"id": "ip_pad_regression", "type": "history",
         "value": "pad_left('7',3,'0')=='007'（step1 行为保持）",
         "locator": "expand.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：slugify 示例驱动
_slug_b = (
    '"""Slug helpers."""\n\n\n'
    "def slugify(s):\n"
    "    return s\n"
)
T(
    id="ind_S06b",
    family="ind_short_examples",
    type="example_driven",
    difficulty="short",
    focus="示例驱动实现 slugify，再扩展 drop_digits",
    files={"names.py": _slug_b},
    steps=[
        {
            "instruction": (
                "实现 names.py 的 slugify(s)：小写、空白段替换为单个连字符、"
                "去掉首尾连字符。示例：slugify('  Hello  World ') == 'hello-world'；"
                "slugify('A_B') == 'a_b'；slugify('Up') == 'up'。"
            ),
            "tests": (
                "import names\n\n\n"
                "def test_spaces():\n"
                '    assert names.slugify("  Hello  World ") == "hello-world"\n\n\n'
                "def test_underscore_kept():\n"
                '    assert names.slugify("A_B") == "a_b"\n\n\n'
                "def test_simple():\n"
                '    assert names.slugify("Up") == "up"\n'
            ),
            "ops": [
                ("replace", "names.py",
                 "def slugify(s):\n    return s\n",
                 "def slugify(s):\n"
                 "    parts = s.lower().split()\n"
                 '    return "-".join(p for p in parts if p)\n'),
            ],
            "expect_targets": {"names.py"},
        },
        {
            "instruction": (
                "names.py 新增 drop_digits(s)：删除所有数字字符后返回。"
                "示例：drop_digits('a1b22') == 'ab'；drop_digits('42') == ''。"
            ),
            "tests": (
                "import names\n\n\n"
                "def test_drop_digits():\n"
                '    assert names.drop_digits("a1b22") == "ab"\n\n\n'
                "def test_all_digits():\n"
                '    assert names.drop_digits("42") == ""\n\n\n'
                "def test_slugify_regression():\n"
                '    assert names.slugify("Hello World") == "hello-world"\n'
            ),
            "ops": [
                ("replace", "names.py",
                 'def slugify(s):\n'
                 '    parts = s.lower().split()\n'
                 '    return "-".join(p for p in parts if p)\n',
                 'def slugify(s):\n'
                 '    parts = s.lower().split()\n'
                 '    return "-".join(p for p in parts if p)\n\n\n'
                 'def drop_digits(s):\n'
                 "    return \"\".join(c for c in s if not c.isdigit())\n"),
            ],
            "expect_targets": {"names.py"},
        },
    ],
    info_points=[
        {"id": "ip_slug_rule", "type": "implementation",
         "value": "lower + 空白段 join '-' + 去首尾 '-'",
         "locator": "instruction:step1 示例",
         "needed_by_steps": [1],
         "redundant_in_instruction": True},
        {"id": "ip_drop_digits_rule", "type": "implementation",
         "value": "删除数字字符",
         "locator": "instruction:step2 示例",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
        {"id": "ip_slug_regression", "type": "history",
         "value": "slugify('Hello World')=='hello-world'（step1 行为保持）",
         "locator": "names.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ SF7 ind_short_repr
# 变体 a：Bag 内部表示 pairs→dict
_bag_a = (
    '"""Tiny store."""\n\n\n'
    "class Bag:\n"
    "    def __init__(self):\n"
    "        self.items = []\n\n"
    "    def put(self, k, v):\n"
    "        self.items.append((k, v))\n\n"
    "    def get(self, k):\n"
    "        for kk, vv in reversed(self.items):\n"
    "            if kk == k:\n"
    "                return vv\n"
    "        return None\n"
)
_bag_new = (
    '"""Tiny store."""\n\n\n'
    "class Bag:\n"
    "    def __init__(self):\n"
    "        self.data = {}\n\n"
    "    def put(self, k, v):\n"
    "        self.data[k] = v\n\n"
    "    def get(self, k):\n"
    "        return self.data.get(k)\n"
)
T(
    id="ind_S07a",
    family="ind_short_repr",
    type="representation_swap",
    difficulty="short",
    focus="Bag 内部表示 pairs 列表换成 self.data 字典",
    files={"store.py": _bag_a},
    steps=[
        {
            "instruction": (
                "修改 store.py 中 Bag 的内部表示：从 pairs 列表换成 self.data 字典"
                "（对外 put/get 行为保持不变；重复 put 同键以最后一次为准）。"
            ),
            "tests": (
                "import store\n\n\n"
                "def test_put_get():\n"
                "    b = store.Bag()\n"
                '    b.put("a", 1)\n'
                '    b.put("b", 2)\n'
                '    assert b.get("a") == 1\n'
                '    assert b.get("missing") is None\n\n\n'
                "def test_last_wins():\n"
                "    b = store.Bag()\n"
                '    b.put("a", 1)\n'
                '    b.put("a", 9)\n'
                '    assert b.get("a") == 9\n\n\n'
                "def test_repr_swapped():\n"
                "    b = store.Bag()\n"
                "    assert isinstance(b.__dict__.get(\"data\"), dict)\n"
                "    assert \"items\" not in b.__dict__\n"
            ),
            "ops": [("replace", "store.py", _bag_a, _bag_new)],
            "expect_targets": {"store.py"},
        },
        {
            "instruction": (
                "store.py 的 Bag 新增 delete(k)：删除键并返回是否真的删除了该键"
                "（内部表示保持不变）。"
            ),
            "tests": (
                "import store\n\n\n"
                "def test_delete():\n"
                "    b = store.Bag()\n"
                '    b.put("a", 1)\n'
                "    assert b.delete(\"a\") is True\n"
                "    assert b.get(\"a\") is None\n"
                "    assert b.delete(\"a\") is False\n\n\n"
                "def test_repr_regression():\n"
                "    b = store.Bag()\n"
                "    assert isinstance(b.__dict__.get(\"data\"), dict)\n\n\n"
                "def test_put_get_regression():\n"
                "    b = store.Bag()\n"
                '    b.put("x", 5)\n'
                '    assert b.get("x") == 5\n'
            ),
            "ops": [
                ("replace", "store.py",
                 "    def get(self, k):\n"
                 "        return self.data.get(k)\n",
                 "    def get(self, k):\n"
                 "        return self.data.get(k)\n\n"
                 "    def delete(self, k):\n"
                 "        if k in self.data:\n"
                 "            del self.data[k]\n"
                 "            return True\n"
                 "        return False\n"),
            ],
            "expect_targets": {"store.py"},
        },
    ],
    info_points=[
        {"id": "ip_bag_repr", "type": "implementation",
         "value": "self.data 字典（self.items 移除）",
         "locator": "instruction:step1 + store.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_last_wins", "type": "interface",
         "value": "重复 put 同键以最后一次为准",
         "locator": "instruction:step1",
         "needed_by_steps": [1],
         "redundant_in_instruction": True},
        {"id": "ip_repr_regression", "type": "history",
         "value": "data 为 dict 且 items 不存在（step1 表示在 step2 后保持）",
         "locator": "store.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：Window 内部表示列表→手动环形缓冲
_win_b = (
    '"""Sliding window."""\n\n\n'
    "class Window:\n"
    "    def __init__(self, capacity):\n"
    "        self.capacity = capacity\n"
    "        self.buf = []\n\n"
    "    def push(self, x):\n"
    "        self.buf.append(x)\n"
    "        if len(self.buf) > self.capacity:\n"
    "            self.buf.pop(0)\n\n"
    "    def values(self):\n"
    "        return list(self.buf)\n"
)
_win_new = (
    '"""Sliding window."""\n\n\n'
    "class Window:\n"
    "    def __init__(self, capacity):\n"
    "        self.capacity = capacity\n"
    "        self.ring = [None] * capacity\n"
    "        self.count = 0\n"
    "        self.head = 0\n\n"
    "    def push(self, x):\n"
    "        idx = (self.head + self.count) % self.capacity\n"
    "        if self.count == self.capacity:\n"
    "            self.ring[self.head] = x\n"
    "            self.head = (self.head + 1) % self.capacity\n"
    "        else:\n"
    "            self.ring[idx] = x\n"
    "            self.count += 1\n\n"
    "    def values(self):\n"
    "        out = []\n"
    "        for i in range(self.count):\n"
    "            out.append(self.ring[(self.head + i) % self.capacity])\n"
    "        return out\n"
)
T(
    id="ind_S07b",
    family="ind_short_repr",
    type="representation_swap",
    difficulty="short",
    focus="Window 内部表示列表换成定长环形缓冲",
    files={"window.py": _win_b},
    steps=[
        {
            "instruction": (
                "修改 window.py 中 Window 的内部表示：从动态列表换成定长环形缓冲"
                "（self.ring 长度等于 capacity，配合 count/head 游标；"
                "对外 push/values 行为保持不变）。"
            ),
            "tests": (
                "import window\n\n\n"
                "def test_under_capacity():\n"
                "    w = window.Window(3)\n"
                "    w.push(1)\n"
                "    w.push(2)\n"
                "    assert w.values() == [1, 2]\n\n\n"
                "def test_overflow():\n"
                "    w = window.Window(3)\n"
                "    for x in (1, 2, 3, 4, 5):\n"
                "        w.push(x)\n"
                "    assert w.values() == [3, 4, 5]\n\n\n"
                "def test_repr_swapped():\n"
                "    w = window.Window(3)\n"
                "    assert isinstance(w.__dict__.get(\"ring\"), list)\n"
                "    assert len(w.ring) == 3\n"
                "    assert \"buf\" not in w.__dict__\n"
            ),
            "ops": [("replace", "window.py", _win_b, _win_new)],
            "expect_targets": {"window.py"},
        },
        {
            "instruction": (
                "window.py 的 Window 新增 size()：返回当前元素个数"
                "（内部表示保持不变）。"
            ),
            "tests": (
                "import window\n\n\n"
                "def test_size():\n"
                "    w = window.Window(3)\n"
                "    w.push(1)\n"
                "    w.push(2)\n"
                "    assert w.size() == 2\n"
                "    w.push(3)\n"
                "    w.push(4)\n"
                "    assert w.size() == 3\n\n\n"
                "def test_repr_regression():\n"
                "    w = window.Window(3)\n"
                "    assert isinstance(w.__dict__.get(\"ring\"), list)\n"
                "    assert \"buf\" not in w.__dict__\n\n\n"
                "def test_values_regression():\n"
                "    w = window.Window(2)\n"
                "    w.push(1)\n"
                "    w.push(2)\n"
                "    w.push(3)\n"
                "    assert w.values() == [2, 3]\n"
            ),
            "ops": [
                ("replace", "window.py",
                 "    def values(self):\n"
                 "        out = []\n"
                 "        for i in range(self.count):\n"
                 "            out.append(self.ring[(self.head + i) % self.capacity])\n"
                 "        return out\n",
                 "    def values(self):\n"
                 "        out = []\n"
                 "        for i in range(self.count):\n"
                 "            out.append(self.ring[(self.head + i) % self.capacity])\n"
                 "        return out\n\n"
                 "    def size(self):\n"
                 "        return self.count\n"),
            ],
            "expect_targets": {"window.py"},
        },
    ],
    info_points=[
        {"id": "ip_ring_repr", "type": "implementation",
         "value": "self.ring + count/head（buf 移除）",
         "locator": "instruction:step1 + window.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_overflow_semantics", "type": "interface",
         "value": "超出容量丢最旧（push 语义不变）",
         "locator": "instruction:step1 + 原实现先例",
         "needed_by_steps": [1],
         "redundant_in_instruction": True},
        {"id": "ip_ring_regression", "type": "history",
         "value": "ring 存在且 buf 不存在（step1 表示在 step2 后保持）",
         "locator": "window.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ SF8 ind_short_format
# 变体 a：kv 解析编解码
_kv_a = (
    '"""Key-value text."""\n\n\n'
    "def format_pair(k, v):\n"
    '    return f"{k}={v}"\n\n\n'
    "def parse_pair(s):\n"
    '    return s.split("=", 1)\n'
)
T(
    id="ind_S08a",
    family="ind_short_format",
    type="parse_format",
    difficulty="short",
    focus="parse_pair 返回元组 + 缺 '=' 抛 ValueError，再扩展 parse_line",
    files={"kv.py": _kv_a},
    steps=[
        {
            "instruction": (
                "kv.py 的 parse_pair(s) 应返回 (key, value) 元组（当前返回列表）；"
                "s 中不含 '=' 时抛 ValueError。"
            ),
            "tests": (
                "import pytest\n\n"
                "import kv\n\n\n"
                "def test_tuple():\n"
                "    out = kv.parse_pair(\"a=1\")\n"
                "    assert isinstance(out, tuple)\n"
                "    assert out == (\"a\", \"1\")\n\n\n"
                "def test_missing_eq():\n"
                "    with pytest.raises(ValueError):\n"
                '        kv.parse_pair("nope")\n\n\n'
                "def test_format_regression():\n"
                '    assert kv.format_pair("a", 1) == "a=1"\n'
            ),
            "ops": [
                ("replace", "kv.py",
                 'def parse_pair(s):\n    return s.split("=", 1)\n',
                 'def parse_pair(s):\n'
                 '    if "=" not in s:\n'
                 '        raise ValueError("missing =")\n'
                 '    k, v = s.split("=", 1)\n'
                 '    return (k, v)\n'),
            ],
            "expect_targets": {"kv.py"},
        },
        {
            "instruction": (
                "kv.py 新增 parse_line(s)：按 ';' 解析多段为字典；"
                "示例：parse_line('a=1;b=2') == {'a': '1', 'b': '2'}；"
                "任一段缺 '=' 时抛 ValueError。"
            ),
            "tests": (
                "import pytest\n\n"
                "import kv\n\n\n"
                "def test_line():\n"
                '    assert kv.parse_line("a=1;b=2") == {"a": "1", "b": "2"}\n\n\n'
                "def test_line_bad_segment():\n"
                "    with pytest.raises(ValueError):\n"
                '        kv.parse_line("a=1;oops")\n\n\n'
                "def test_pair_regression():\n"
                '    assert kv.parse_pair("a=1") == ("a", "1")\n'
            ),
            "ops": [
                ("replace", "kv.py",
                 'def parse_pair(s):\n'
                 '    if "=" not in s:\n'
                 '        raise ValueError("missing =")\n'
                 '    k, v = s.split("=", 1)\n'
                 '    return (k, v)\n',
                 'def parse_pair(s):\n'
                 '    if "=" not in s:\n'
                 '        raise ValueError("missing =")\n'
                 '    k, v = s.split("=", 1)\n'
                 '    return (k, v)\n\n\n'
                 'def parse_line(s):\n'
                 '    out = {}\n'
                 '    for seg in s.split(";"):\n'
                 '        k, v = parse_pair(seg)\n'
                 '        out[k] = v\n'
                 '    return out\n'),
            ],
            "expect_targets": {"kv.py"},
        },
    ],
    info_points=[
        {"id": "ip_pair_contract", "type": "interface",
         "value": "parse_pair 返回元组；缺 '=' 抛 ValueError",
         "locator": "instruction:step1 + kv.py",
         "needed_by_steps": [1],
         "redundant_in_instruction": True},
        {"id": "ip_line_spec", "type": "implementation",
         "value": "';' 分段复用 parse_pair 组字典",
         "locator": "instruction:step2 示例",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
        {"id": "ip_pair_regression", "type": "history",
         "value": "parse_pair('a=1')==('a','1')（step1 契约保持）",
         "locator": "kv.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：日期格式化/解析往返
_date_b = (
    '"""Dates."""\n\n\n'
    "def format_date(y, m, d):\n"
    '    return f"{y}-{m}-{d}"\n'
)
T(
    id="ind_S08b",
    family="ind_short_format",
    type="parse_format",
    difficulty="short",
    focus="format_date 补零规范 + parse_date 逆变换",
    files={"datefmt.py": _date_b},
    steps=[
        {
            "instruction": (
                "datefmt.py 的 format_date(y, m, d) 应返回补零的 'YYYY-MM-DD'"
                "（当前月/日未补零，例如 2024-3-5 应变为 2024-03-05）。"
            ),
            "tests": (
                "import datefmt\n\n\n"
                "def test_pad():\n"
                '    assert datefmt.format_date(2024, 3, 5) == "2024-03-05"\n\n\n'
                "def test_already_padded():\n"
                '    assert datefmt.format_date(1999, 12, 31) == "1999-12-31"\n'
            ),
            "ops": [
                ("replace", "datefmt.py",
                 'def format_date(y, m, d):\n    return f"{y}-{m}-{d}"\n',
                 'def format_date(y, m, d):\n'
                 '    return f"{y:04d}-{m:02d}-{d:02d}"\n'),
            ],
            "expect_targets": {"datefmt.py"},
        },
        {
            "instruction": (
                "datefmt.py 新增 parse_date(s)：解析 'YYYY-MM-DD' 返回 (y, m, d) 元组；"
                "格式不符（非10位、分隔符错、含非数字）时抛 ValueError。"
            ),
            "tests": (
                "import pytest\n\n"
                "import datefmt\n\n\n"
                "def test_parse():\n"
                '    assert datefmt.parse_date("2024-03-05") == (2024, 3, 5)\n\n\n'
                "def test_parse_bad():\n"
                "    with pytest.raises(ValueError):\n"
                '        datefmt.parse_date("2024/03/05")\n'
                "    with pytest.raises(ValueError):\n"
                '        datefmt.parse_date("not-a-date")\n\n\n'
                "def test_format_regression():\n"
                '    assert datefmt.format_date(2024, 3, 5) == "2024-03-05"\n'
            ),
            "ops": [
                ("replace", "datefmt.py",
                 'def format_date(y, m, d):\n'
                 '    return f"{y:04d}-{m:02d}-{d:02d}"\n',
                 'def format_date(y, m, d):\n'
                 '    return f"{y:04d}-{m:02d}-{d:02d}"\n\n\n'
                 'def parse_date(s):\n'
                 '    if len(s) != 10 or s[4] != "-" or s[7] != "-":\n'
                 '        raise ValueError("bad format")\n'
                 '    y, m, d = s[:4], s[5:7], s[8:10]\n'
                 '    if not (y.isdigit() and m.isdigit() and d.isdigit()):\n'
                 '        raise ValueError("bad digits")\n'
                 '    return (int(y), int(m), int(d))\n'),
            ],
            "expect_targets": {"datefmt.py"},
        },
    ],
    info_points=[
        {"id": "ip_date_format", "type": "implementation",
         "value": "YYYY-MM-DD 补零",
         "locator": "instruction:step1 + datefmt.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_parse_contract", "type": "interface",
         "value": "parse_date 返回 (y,m,d)，坏格式抛 ValueError",
         "locator": "instruction:step2",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
        {"id": "ip_format_regression", "type": "history",
         "value": "format_date(2024,3,5)=='2024-03-05'（step1 规范保持）",
         "locator": "datefmt.py (step1) + step2 回归 eval",
         "needed_by_steps": [2],
         "redundant_in_instruction": False},
    ],
)
