"""独立任务集 Medium 族（Part2 independent-v1）：8 archetype × 2 变体 = 16 题，每题 5 步。

结构独立于 P1：bug 链 / JSON 模式演进 / 状态机 / 缓存策略 / 类层级 / 解析器文法 /
多阶段管道 / 注册表分派。变体间骨架不同（非纯换名）。
"""

from registry import T

# ============================================================ MF1 ind_med_bugchain
# 变体 a：运费报价关联 bug 链（百分比 → 免邮阈值 → 钳制 → 负重量 → 批量）
_ship_a = (
    '"""Shipping quotes."""\n\n'
    "BASE_RATE = 8\n"
    "FREE_AT = 500\n\n\n"
    "def weight_fee(weight):\n"
    "    if weight <= 4:\n"
    "        return BASE_RATE\n"
    "    return BASE_RATE + (weight - 4) * 3\n\n\n"
    "def surcharge(subtotal, pct):\n"
    "    return subtotal * pct\n\n\n"
    "def quote(subtotal, weight, pct):\n"
    "    return weight_fee(weight) + surcharge(subtotal, pct)\n"
)
_inv_a = (
    '"""Invoice helpers."""\n\n'
    "from shipping import quote\n\n\n"
    "def order_total(subtotal, weight, pct):\n"
    "    return quote(subtotal, weight, pct)\n"
)
_s1_old = "    return subtotal * pct\n"
_s1_new = "    return subtotal * pct / 100.0\n"
_s2_old = (
    "def quote(subtotal, weight, pct):\n"
    "    return weight_fee(weight) + surcharge(subtotal, pct)\n"
)
_s2_new = (
    "def quote(subtotal, weight, pct):\n"
    '    fee = 0 if subtotal >= FREE_AT else weight_fee(weight)\n'
    "    return fee + surcharge(subtotal, pct)\n"
)
_s3_old = (
    "def surcharge(subtotal, pct):\n"
    "    return subtotal * pct / 100.0\n"
)
_s3_new = (
    "def surcharge(subtotal, pct):\n"
    "    if pct < 0:\n"
    "        pct = 0\n"
    "    if pct > 100:\n"
    "        pct = 100\n"
    "    return subtotal * pct / 100.0\n"
)
_s4_old = (
    "def weight_fee(weight):\n"
    "    if weight <= 4:\n"
    "        return BASE_RATE\n"
)
_s4_new = (
    "def weight_fee(weight):\n"
    "    if weight < 0:\n"
    '        raise ValueError("weight")\n'
    "    if weight <= 4:\n"
    "        return BASE_RATE\n"
)
_s5_old = (
    "def order_total(subtotal, weight, pct):\n"
    "    return quote(subtotal, weight, pct)\n"
)
_s5_new = (
    "def order_total(subtotal, weight, pct):\n"
    "    return quote(subtotal, weight, pct)\n\n\n"
    "def batch_total(rows):\n"
    "    return sum(order_total(s, w, p) for s, w, p in rows)\n"
)
T(
    id="ind_M01a",
    family="ind_med_bugchain",
    type="bugfix_chain",
    difficulty="medium",
    focus="运费报价 5 步 bug 链：百分比语义→免邮阈值→pct 钳制→负重量→批量求和",
    files={"shipping.py": _ship_a, "invoice.py": _inv_a},
    steps=[
        {
            "instruction": (
                "请修改 shipping.py 中的 surcharge(subtotal, pct)："
                "pct 是百分数（15 表示 15%），当前把 15 当成 15.0 倍使用。"
            ),
            "tests": (
                "import shipping\n\n\n"
                "def test_surcharge_pct():\n"
                "    assert shipping.surcharge(200, 15) == 30.0\n\n\n"
                "def test_surcharge_zero():\n"
                "    assert shipping.surcharge(200, 0) == 0.0\n\n\n"
                "def test_weight_fee_regression():\n"
                "    assert shipping.weight_fee(3) == 8\n"
            ),
            "ops": [("replace", "shipping.py", _s1_old, _s1_new)],
            "expect_targets": {"shipping.py"},
        },
        {
            "instruction": (
                "请修改 shipping.py 中的 quote(subtotal, weight, pct)："
                "subtotal 达到 FREE_AT 及以上时应免除 weight_fee"
                "（当前始终计入运费）。"
            ),
            "tests": (
                "import shipping\n\n\n"
                "def test_free_shipment():\n"
                "    assert shipping.quote(600, 10, 10) == 60.0\n\n\n"
                "def test_below_threshold():\n"
                "    assert shipping.quote(100, 3, 10) == 18.0\n\n\n"
                "def test_surcharge_regression():\n"
                "    assert shipping.surcharge(200, 15) == 30.0\n"
            ),
            "ops": [("replace", "shipping.py", _s2_old, _s2_new)],
            "expect_targets": {"shipping.py"},
        },
        {
            "instruction": (
                "请修改 shipping.py 中的 surcharge(subtotal, pct)："
                "pct 小于 0 时按 0 处理，大于 100 时按 100 处理。"
            ),
            "tests": (
                "import shipping\n\n\n"
                "def test_clamp_high():\n"
                "    assert shipping.surcharge(100, 150) == 100.0\n\n\n"
                "def test_clamp_low():\n"
                "    assert shipping.surcharge(100, -5) == 0.0\n\n\n"
                "def test_normal_regression():\n"
                "    assert shipping.surcharge(200, 15) == 30.0\n"
            ),
            "ops": [("replace", "shipping.py", _s3_old, _s3_new)],
            "expect_targets": {"shipping.py"},
        },
        {
            "instruction": (
                "请修改 shipping.py 中的 weight_fee(weight)："
                "weight 为负数时应抛出 ValueError（当前照常返回费用）。"
            ),
            "tests": (
                "import pytest\n\n"
                "import shipping\n\n\n"
                "def test_negative_weight():\n"
                "    with pytest.raises(ValueError):\n"
                "        shipping.weight_fee(-1)\n\n\n"
                "def test_quote_negative():\n"
                "    with pytest.raises(ValueError):\n"
                "        shipping.quote(100, -2, 10)\n\n\n"
                "def test_free_regression():\n"
                "    assert shipping.quote(600, 10, 10) == 60.0\n"
            ),
            "ops": [("replace", "shipping.py", _s4_old, _s4_new)],
            "expect_targets": {"shipping.py"},
        },
        {
            "instruction": (
                "invoice.py 新增 batch_total(rows)：rows 为 "
                "(subtotal, weight, pct) 三元组列表，对每行调用 order_total "
                "并返回总和；空列表返回 0。"
            ),
            "tests": (
                "import invoice\n\n\n"
                "def test_batch():\n"
                "    rows = [(100, 3, 10), (600, 10, 10)]\n"
                "    assert invoice.batch_total(rows) == 78.0\n\n\n"
                "def test_batch_empty():\n"
                "    assert invoice.batch_total([]) == 0\n\n\n"
                "def test_order_regression():\n"
                "    assert invoice.order_total(100, 3, 10) == 18.0\n"
            ),
            "ops": [("replace", "invoice.py", _s5_old, _s5_new)],
            "expect_targets": {"invoice.py"},
        },
    ],
    info_points=[
        {"id": "ip_surcharge_pct", "type": "implementation",
         "value": "surcharge = subtotal * pct / 100.0",
         "locator": "instruction:step1 + shipping.py",
         "needed_by_steps": [1, 2, 3],
         "redundant_in_instruction": True},
        {"id": "ip_free_at", "type": "critical_data",
         "value": "FREE_AT=500 时免除 weight_fee",
         "locator": "instruction:step2 + shipping.py",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
        {"id": "ip_free_regression", "type": "history",
         "value": "quote(600,10,10)==60.0（step2 免邮在 step3-5 后保持）",
         "locator": "shipping.py (step2) + step5 回归 eval",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": False},
        {"id": "ip_batch_contract", "type": "interface",
         "value": "batch_total 对每行 order_total 求和",
         "locator": "instruction:step5 + invoice.py",
         "needed_by_steps": [5],
         "redundant_in_instruction": True},
    ],
)

# 变体 b：成绩报告关联 bug 链（百分数刻度 → 调用方同步 → 等级档位 → 除零 → 平均）
_grd_b = (
    '"""Grade book."""\n\n\n'
    "def pct(correct, total):\n"
    "    return correct / total\n\n\n"
    "def letter(score):\n"
    "    if score >= 90:\n"
    '        return "A"\n'
    "    if score >= 80:\n"
    '        return "B"\n'
    "    if score >= 70:\n"
    '        return "C"\n'
    '    return "D"\n'
)
_rep_b = (
    '"""Report card."""\n\n'
    "from grades import pct, letter\n\n\n"
    "def line(correct, total):\n"
    "    return letter(pct(correct, total) * 100)\n"
)
_g1_old = "    return correct / total\n"
_g1_new = "    return correct * 100.0 / total\n"
_g2_old = "    return letter(pct(correct, total) * 100)\n"
_g2_new = "    return letter(pct(correct, total))\n"
_g3_old = (
    "def letter(score):\n"
    "    if score >= 90:\n"
    '        return "A"\n'
    "    if score >= 80:\n"
    '        return "B"\n'
    "    if score >= 70:\n"
    '        return "C"\n'
    '    return "D"\n'
)
_g3_new = (
    "def letter(score):\n"
    "    if score >= 90:\n"
    '        return "A"\n'
    "    if score >= 80:\n"
    '        return "B"\n'
    "    if score >= 70:\n"
    '        return "C"\n'
    "    if score >= 60:\n"
    '        return "D"\n'
    '    return "F"\n'
)
_g4_old = (
    "def pct(correct, total):\n"
    "    return correct * 100.0 / total\n"
)
_g4_new = (
    "def pct(correct, total):\n"
    "    if total <= 0:\n"
    '        raise ValueError("total")\n'
    "    return correct * 100.0 / total\n"
)
_g5_old = (
    "def line(correct, total):\n"
    "    return letter(pct(correct, total))\n"
)
_g5_new = (
    "def line(correct, total):\n"
    "    return letter(pct(correct, total))\n\n\n"
    "def average_score(rows):\n"
    "    if not rows:\n"
    "        return 0.0\n"
    "    return sum(pct(c, t) for c, t in rows) / len(rows)\n"
)
T(
    id="ind_M01b",
    family="ind_med_bugchain",
    type="bugfix_chain",
    difficulty="medium",
    focus="成绩报告 5 步 bug 链：百分数刻度→调用方同步→F 档→total 校验→平均分",
    files={"grades.py": _grd_b, "report.py": _rep_b},
    steps=[
        {
            "instruction": (
                "请修改 grades.py 中的 pct(correct, total)："
                "应返回百分数（90 表示 90%），当前返回 0 到 1 的小数。"
            ),
            "tests": (
                "import grades\n\n\n"
                "def test_pct_scale():\n"
                "    assert grades.pct(9, 10) == 90.0\n\n\n"
                "def test_pct_full():\n"
                "    assert grades.pct(10, 10) == 100.0\n\n\n"
                "def test_letter_regression():\n"
                '    assert grades.letter(85) == "B"\n'
            ),
            "ops": [("replace", "grades.py", _g1_old, _g1_new)],
            "expect_targets": {"grades.py"},
        },
        {
            "instruction": (
                "请修改 report.py 中的 line(correct, total)："
                "当前对百分数结果又乘了一次 100，导致等级输出错误。"
            ),
            "tests": (
                "import report\n"
                "import grades\n\n\n"
                "def test_line_ok():\n"
                '    assert report.line(8, 10) == "B"\n\n\n'
                "def test_line_high():\n"
                '    assert report.line(9, 10) == "A"\n\n\n'
                "def test_pct_regression():\n"
                "    assert grades.pct(7, 10) == 70.0\n"
            ),
            "ops": [("replace", "report.py", _g2_old, _g2_new)],
            "expect_targets": {"report.py"},
        },
        {
            "instruction": (
                "请修改 grades.py 中的 letter(score)："
                "60 到 69 应返回 D，低于 60 应返回 F"
                "（当前低于 70 都返回 D）。"
            ),
            "tests": (
                "import grades\n"
                "import report\n\n\n"
                "def test_d_range():\n"
                '    assert grades.letter(65) == "D"\n\n\n'
                "def test_f_range():\n"
                '    assert grades.letter(40) == "F"\n\n\n'
                "def test_line_regression():\n"
                '    assert report.line(8, 10) == "B"\n'
            ),
            "ops": [("replace", "grades.py", _g3_old, _g3_new)],
            "expect_targets": {"grades.py"},
        },
        {
            "instruction": (
                "请修改 grades.py 中的 pct(correct, total)："
                "total 小于等于 0 时应抛出 ValueError"
                "（当前抛出 ZeroDivisionError）。"
            ),
            "tests": (
                "import pytest\n\n"
                "import grades\n\n\n"
                "def test_zero_total():\n"
                "    with pytest.raises(ValueError):\n"
                "        grades.pct(5, 0)\n\n\n"
                "def test_negative_total():\n"
                "    with pytest.raises(ValueError):\n"
                "        grades.pct(5, -1)\n\n\n"
                "def test_ok_regression():\n"
                "    assert grades.pct(9, 10) == 90.0\n"
            ),
            "ops": [("replace", "grades.py", _g4_old, _g4_new)],
            "expect_targets": {"grades.py"},
        },
        {
            "instruction": (
                "report.py 新增 average_score(rows)：rows 为 (correct, total) "
                "列表，返回各行百分数得分的平均值；空列表返回 0.0。"
            ),
            "tests": (
                "import report\n\n\n"
                "def test_average():\n"
                "    rows = [(8, 10), (9, 10)]\n"
                "    assert report.average_score(rows) == 85.0\n\n\n"
                "def test_average_empty():\n"
                "    assert report.average_score([]) == 0.0\n\n\n"
                "def test_line_regression():\n"
                '    assert report.line(7, 10) == "C"\n'
            ),
            "ops": [("replace", "report.py", _g5_old, _g5_new)],
            "expect_targets": {"report.py"},
        },
    ],
    info_points=[
        {"id": "ip_pct_scale", "type": "implementation",
         "value": "pct = correct * 100.0 / total",
         "locator": "instruction:step1 + grades.py",
         "needed_by_steps": [1, 2, 5],
         "redundant_in_instruction": True},
        {"id": "ip_letter_f", "type": "implementation",
         "value": "letter: 60-69→D，<60→F",
         "locator": "instruction:step3 + grades.py",
         "needed_by_steps": [3],
         "redundant_in_instruction": True},
        {"id": "ip_pct_history", "type": "history",
         "value": "pct(9,10)==90.0（step1 刻度在 step4-5 后保持）",
         "locator": "grades.py (step1) + step5 回归 eval",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": False},
        {"id": "ip_avg_contract", "type": "interface",
         "value": "average_score 对各行 pct 取平均，空表 0.0",
         "locator": "instruction:step5 + report.py",
         "needed_by_steps": [5],
         "redundant_in_instruction": True},
    ],
)

# ============================================================ MF2 ind_med_schema
# 变体 a：人员记录 JSON 模式 v1→v2（默认值/校验/导出/键名迁移）
_people_a = (
    "[\n"
    '  {"name": "Ann", "age": 30},\n'
    '  {"name": "Bo", "age": 25},\n'
    '  {"name": "Cy"}\n'
    "]\n"
)
_loader_a = (
    '"""Record loading."""\n\n'
    "import json\n"
    "from pathlib import Path\n\n\n"
    'def defaults():\n'
    '    return {"name": "", "age": 0}\n\n\n'
    'def load(path="people.json"):\n'
    "    base = Path(__file__).resolve().parent\n"
    "    target = Path(path)\n"
    "    if not target.is_absolute():\n"
    "        target = base / target\n"
    '    return json.loads(target.read_text(encoding="utf-8"))\n'
)
_exp_a = (
    '"""Export helpers."""\n\n'
    "from loader import load\n\n\n"
    "def names():\n"
    '    return [r["name"] for r in load()]\n'
)
_l1_old = '    return json.loads(target.read_text(encoding="utf-8"))\n'
_l1_new = (
    '    rows = json.loads(target.read_text(encoding="utf-8"))\n'
    "    out = []\n"
    "    for r in rows:\n"
    "        row = dict(defaults())\n"
    "        row.update(r)\n"
    "        out.append(row)\n"
    "    return out\n"
)
_l2_old = (
    "    for r in rows:\n"
    "        row = dict(defaults())\n"
    "        row.update(r)\n"
    "        out.append(row)\n"
    "    return out\n"
)
_l2_new = (
    "    for r in rows:\n"
    "        row = dict(defaults())\n"
    "        row.update(r)\n"
    "        if not isinstance(row[\"age\"], int):\n"
    '            raise ValueError("age")\n'
    "        out.append(row)\n"
    "    return out\n"
)
_e3_old = (
    "def names():\n"
    '    return [r["name"] for r in load()]\n'
)
_e3_new = (
    "def names():\n"
    '    return [r["name"] for r in load()]\n\n\n'
    "def ages():\n"
    '    return [r["age"] for r in load()]\n'
)
_people_v2 = (
    "[\n"
    '  {"full_name": "Ann", "age": 30},\n'
    '  {"full_name": "Bo", "age": 25},\n'
    '  {"full_name": "Cy"}\n'
    "]\n"
)
_l4_old = '    return {"name": "", "age": 0}\n'
_l4_new = '    return {"full_name": "", "age": 0}\n'
_e5_old = '    return [r["name"] for r in load()]\n'
_e5_new = '    return [r["full_name"] for r in load()]\n'
T(
    id="ind_M02a",
    family="ind_med_schema",
    type="json_schema_evolution",
    difficulty="medium",
    focus="人员记录模式演进：loader 默认值→age 校验→导出 ages→v2 键名迁移→消费方同步",
    files={"people.json": _people_a, "loader.py": _loader_a, "export.py": _exp_a},
    steps=[
        {
            "instruction": (
                "请修改 loader.py 中的 load(path)：返回记录前用 defaults() "
                "补齐缺失的键（当前缺 age 的记录直接透传）。"
            ),
            "tests": (
                "import loader\n\n\n"
                "def test_defaults_applied():\n"
                "    rows = loader.load()\n"
                "    cy = [r for r in rows if r[\"name\"] == \"Cy\"][0]\n"
                "    assert cy[\"age\"] == 0\n\n\n"
                "def test_existing_kept():\n"
                "    ann = loader.load()[0]\n"
                "    assert ann[\"age\"] == 30\n"
                '    assert ann["name"] == "Ann"\n'
            ),
            "ops": [("replace", "loader.py", _l1_old, _l1_new)],
            "expect_targets": {"loader.py"},
        },
        {
            "instruction": (
                "请修改 loader.py 中的 load(path)："
                "age 不是整数时应抛出 ValueError"
                '（字符串 "30" 也不接受）。'
            ),
            "tests": (
                "import json\n"
                "import pytest\n"
                "import loader\n\n\n"
                "def test_bad_age(tmp_path):\n"
                '    p = tmp_path / "p.json"\n'
                '    p.write_text(json.dumps([{"name": "X", "age": "30"}]),\n'
                '                 encoding="utf-8")\n'
                "    with pytest.raises(ValueError):\n"
                "        loader.load(str(p))\n\n\n"
                "def test_good_age(tmp_path):\n"
                '    p = tmp_path / "p.json"\n'
                '    p.write_text(json.dumps([{"name": "X", "age": 7}]),\n'
                '                 encoding="utf-8")\n'
                '    assert loader.load(str(p))[0]["age"] == 7\n\n\n'
                "def test_defaults_regression():\n"
                "    rows = loader.load()\n"
                '    assert rows[2]["age"] == 0\n'
            ),
            "ops": [("replace", "loader.py", _l2_old, _l2_new)],
            "expect_targets": {"loader.py"},
        },
        {
            "instruction": (
                "export.py 新增 ages()：返回所有记录的 age 列表"
                "（顺序与读入顺序一致）。"
            ),
            "tests": (
                "import export\n\n\n"
                "def test_ages():\n"
                "    assert export.ages() == [30, 25, 0]\n\n\n"
                "def test_names_regression():\n"
                '    assert export.names() == ["Ann", "Bo", "Cy"]\n'
            ),
            "ops": [("replace", "export.py", _e3_old, _e3_new)],
            "expect_targets": {"export.py"},
        },
        {
            "instruction": (
                "people.json 迁移到 v2 键名：name 应为 full_name；"
                "loader.py 的 defaults() 同步使用 full_name。"
            ),
            "tests": (
                "import loader\n\n\n"
                "def test_v2_default_key():\n"
                '    assert "full_name" in loader.defaults()\n'
                '    assert "name" not in loader.defaults()\n\n\n'
                "def test_load_returns_v2():\n"
                "    rows = loader.load()\n"
                '    assert rows[0]["full_name"] == "Ann"\n'
                '    assert "name" not in rows[0]\n'
            ),
            "ops": [
                ("replace", "people.json", _people_a, _people_v2),
                ("replace", "loader.py", _l4_old, _l4_new),
            ],
            "expect_targets": {"people.json", "loader.py"},
        },
        {
            "instruction": (
                "请修改 export.py 中的 names()："
                "应改读 full_name 键（当前仍读 name 导致 KeyError）。"
            ),
            "tests": (
                "import export\n"
                "import loader\n\n\n"
                "def test_names_v2():\n"
                '    assert export.names() == ["Ann", "Bo", "Cy"]\n\n\n'
                "def test_ages_regression():\n"
                "    assert export.ages() == [30, 25, 0]\n\n\n"
                "def test_defaults_regression():\n"
                '    assert "full_name" in loader.defaults()\n'
            ),
            "ops": [("replace", "export.py", _e5_old, _e5_new)],
            "expect_targets": {"export.py"},
        },
    ],
    info_points=[
        {"id": "ip_defaults_merge", "type": "implementation",
         "value": "load 用 defaults() 补齐缺失键",
         "locator": "instruction:step1 + loader.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_age_validate", "type": "implementation",
         "value": "age 非 int → ValueError",
         "locator": "instruction:step2 + loader.py",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
        {"id": "ip_v2_keyname", "type": "critical_data",
         "value": "v2 键名 full_name（取代 name）",
         "locator": "instruction:step4 + people.json",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": True},
        {"id": "ip_cy_age_history", "type": "history",
         "value": "load() 后 Cy.age==0（step1 行为在 step2-4 后保持）",
         "locator": "loader.py (step1) + step5 回归 eval",
         "needed_by_steps": [2, 5],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：商品目录 JSON 模式（price 默认值/校验/导出/迁移到 cost_cents）
_items_b = (
    "{\n"
    '  "a1": {"title": "Pen", "price": 2},\n'
    '  "a2": {"title": "Pad", "price": 5}\n'
    "}\n"
)
_cat_b = (
    '"""Catalog loading."""\n\n'
    "import json\n"
    "from pathlib import Path\n\n\n"
    'def load(path="items.json"):\n'
    "    base = Path(__file__).resolve().parent\n"
    "    target = Path(path)\n"
    "    if not target.is_absolute():\n"
    "        target = base / target\n"
    '    return json.loads(target.read_text(encoding="utf-8"))\n'
)
_tot_b = (
    '"""Totals."""\n\n'
    "from catalog import load\n\n\n"
    "def sum_prices():\n"
    "    data = load()\n"
    '    return sum(r["price"] for r in data.values())\n'
)
_c1_old = '    return json.loads(target.read_text(encoding="utf-8"))\n'
_c1_new = (
    '    data = json.loads(target.read_text(encoding="utf-8"))\n'
    "    out = {}\n"
    "    for k, r in data.items():\n"
    "        row = dict(r)\n"
    '        row.setdefault("price", 0)\n'
    "        out[k] = row\n"
    "    return out\n"
)
_c2_old = (
    "    for k, r in data.items():\n"
    "        row = dict(r)\n"
    '        row.setdefault("price", 0)\n'
    "        out[k] = row\n"
    "    return out\n"
)
_c2_new = (
    "    for k, r in data.items():\n"
    "        row = dict(r)\n"
    '        row.setdefault("price", 0)\n'
    '        if not isinstance(row["price"], (int, float)):\n'
    '            raise ValueError("price")\n'
    "        out[k] = row\n"
    "    return out\n"
)
_t3_old = (
    "def sum_prices():\n"
    "    data = load()\n"
    '    return sum(r["price"] for r in data.values())\n'
)
_t3_new = (
    "def sum_prices():\n"
    "    data = load()\n"
    '    return sum(r["price"] for r in data.values())\n\n\n'
    "def count_items():\n"
    "    return len(load())\n"
)
_items_v2 = (
    "{\n"
    '  "a1": {"title": "Pen", "cost_cents": 200},\n'
    '  "a2": {"title": "Pad", "cost_cents": 500}\n'
    "}\n"
)
_c4_old = (
    "        row = dict(r)\n"
    '        row.setdefault("price", 0)\n'
    '        if not isinstance(row["price"], (int, float)):\n'
    '            raise ValueError("price")\n'
)
_c4_new = (
    "        row = dict(r)\n"
    '        row.setdefault("cost_cents", 0)\n'
    '        if not isinstance(row["cost_cents"], int):\n'
    '            raise ValueError("cost_cents")\n'
)
_t5_old = '    return sum(r["price"] for r in data.values())\n'
_t5_new = '    return sum(r["cost_cents"] for r in data.values())\n'
T(
    id="ind_M02b",
    family="ind_med_schema",
    type="json_schema_evolution",
    difficulty="medium",
    focus="商品目录模式演进：price 默认值→类型校验→count 导出→cost_cents 迁移→求和同步",
    files={"items.json": _items_b, "catalog.py": _cat_b, "totals.py": _tot_b},
    steps=[
        {
            "instruction": (
                "请修改 catalog.py 中的 load(path)："
                "记录缺少 price 键时应补默认值 0"
                "（当前直接透传缺键记录）。"
            ),
            "tests": (
                "import json\n"
                "import catalog\n\n\n"
                "def test_default_price(tmp_path):\n"
                '    p = tmp_path / "i.json"\n'
                '    p.write_text(json.dumps({"k": {"title": "T"}}),\n'
                '                 encoding="utf-8")\n'
                '    assert catalog.load(str(p))["k"]["price"] == 0\n\n\n'
                "def test_existing_price():\n"
                '    assert catalog.load()["a1"]["price"] == 2\n'
            ),
            "ops": [("replace", "catalog.py", _c1_old, _c1_new)],
            "expect_targets": {"catalog.py"},
        },
        {
            "instruction": (
                "请修改 catalog.py 中的 load(path)："
                "price 不是数值时应抛出 ValueError"
                '（字符串 "2" 也不接受）。'
            ),
            "tests": (
                "import json\n"
                "import pytest\n"
                "import catalog\n\n\n"
                "def test_bad_price(tmp_path):\n"
                '    p = tmp_path / "i.json"\n'
                '    p.write_text(json.dumps({"k": {"price": "2"}}),\n'
                '                 encoding="utf-8")\n'
                "    with pytest.raises(ValueError):\n"
                "        catalog.load(str(p))\n\n\n"
                "def test_default_regression(tmp_path):\n"
                '    p = tmp_path / "i.json"\n'
                '    p.write_text(json.dumps({"k": {"title": "T"}}),\n'
                '                 encoding="utf-8")\n'
                '    assert catalog.load(str(p))["k"]["price"] == 0\n'
            ),
            "ops": [("replace", "catalog.py", _c2_old, _c2_new)],
            "expect_targets": {"catalog.py"},
        },
        {
            "instruction": (
                "totals.py 新增 count_items()：返回目录中记录条数。"
            ),
            "tests": (
                "import totals\n\n\n"
                "def test_count():\n"
                "    assert totals.count_items() == 2\n\n\n"
                "def test_sum_regression():\n"
                "    assert totals.sum_prices() == 7\n"
            ),
            "ops": [("replace", "totals.py", _t3_old, _t3_new)],
            "expect_targets": {"totals.py"},
        },
        {
            "instruction": (
                "items.json 迁移到 v2：price 应为 cost_cents（值改为分，"
                "2 → 200，5 → 500）；catalog.py 的校验与默认键同步使用 cost_cents。"
            ),
            "tests": (
                "import catalog\n\n\n"
                "def test_v2_values():\n"
                "    data = catalog.load()\n"
                '    assert data["a1"]["cost_cents"] == 200\n'
                '    assert data["a2"]["cost_cents"] == 500\n'
                '    assert "price" not in data["a1"]\n\n\n'
                "def test_v2_default(tmp_path):\n"
                "    import json\n"
                '    p = tmp_path / "i.json"\n'
                '    p.write_text(json.dumps({"k": {"title": "T"}}),\n'
                '                 encoding="utf-8")\n'
                '    assert catalog.load(str(p))["k"]["cost_cents"] == 0\n'
            ),
            "ops": [
                ("replace", "items.json", _items_b, _items_v2),
                ("replace", "catalog.py", _c4_old, _c4_new),
            ],
            "expect_targets": {"items.json", "catalog.py"},
        },
        {
            "instruction": (
                "请修改 totals.py 中的 sum_prices()："
                "应改读 cost_cents 并返回分单位总和"
                "（当前读 price 导致 KeyError）。"
            ),
            "tests": (
                "import totals\n"
                "import catalog\n\n\n"
                "def test_sum_cents():\n"
                "    assert totals.sum_prices() == 700\n\n\n"
                "def test_count_regression():\n"
                "    assert totals.count_items() == 2\n\n\n"
                "def test_catalog_regression():\n"
                '    assert catalog.load()["a1"]["cost_cents"] == 200\n'
            ),
            "ops": [("replace", "totals.py", _t5_old, _t5_new)],
            "expect_targets": {"totals.py"},
        },
    ],
    info_points=[
        {"id": "ip_price_default", "type": "implementation",
         "value": "缺 price → setdefault 0",
         "locator": "instruction:step1 + catalog.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_price_validate", "type": "implementation",
         "value": "price 非数值 → ValueError",
         "locator": "instruction:step2 + catalog.py",
         "needed_by_steps": [2],
         "redundant_in_instruction": True},
        {"id": "ip_cents_key", "type": "critical_data",
         "value": "v2 键 cost_cents，值为分（200/500）",
         "locator": "instruction:step4 + items.json",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": True},
        {"id": "ip_count_history", "type": "history",
         "value": "count_items()==2（step3 在键名迁移后保持）",
         "locator": "totals.py (step3) + step5 回归 eval",
         "needed_by_steps": [5],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ MF3 ind_med_state
# 变体 a：订单状态机（pay→ship→cancel→终端→refund→可用动作）
_ord_a = (
    '"""Order states."""\n\n\n'
    "def advance(state, action):\n"
    '    if state == "new" and action == "pay":\n'
    '        return "paid"\n'
    "    return state\n\n\n"
    "def can_cancel(state):\n"
    '    return state in ("new", "paid")\n'
)
_o1_old = (
    "def advance(state, action):\n"
    '    if state == "new" and action == "pay":\n'
    '        return "paid"\n'
    "    return state\n"
)
_o1_new = (
    "def advance(state, action):\n"
    '    if state == "new" and action == "pay":\n'
    '        return "paid"\n'
    '    if state == "paid" and action == "ship":\n'
    '        return "shipped"\n'
    "    return state\n"
)
_o2_old = (
    '    if state == "paid" and action == "ship":\n'
    '        return "shipped"\n'
    "    return state\n"
)
_o2_new = (
    '    if state == "paid" and action == "ship":\n'
    '        return "shipped"\n'
    '    if action == "cancel" and can_cancel(state):\n'
    '        return "cancelled"\n'
    "    return state\n"
)
_o3_old = (
    "def advance(state, action):\n"
    '    if state == "new" and action == "pay":\n'
    '        return "paid"\n'
)
_o3_new = (
    "def advance(state, action):\n"
    '    if state in ("shipped", "cancelled"):\n'
    '        raise ValueError("terminal")\n'
    '    if state == "new" and action == "pay":\n'
    '        return "paid"\n'
)
_o4_old = (
    '    if state in ("shipped", "cancelled"):\n'
    '        raise ValueError("terminal")\n'
    '    if state == "new" and action == "pay":\n'
    '        return "paid"\n'
    '    if state == "paid" and action == "ship":\n'
    '        return "shipped"\n'
    '    if action == "cancel" and can_cancel(state):\n'
    '        return "cancelled"\n'
    "    return state\n"
)
_o4_new = (
    '    if state in ("cancelled", "refunded"):\n'
    '        raise ValueError("terminal")\n'
    '    if state == "new" and action == "pay":\n'
    '        return "paid"\n'
    '    if state == "paid" and action == "ship":\n'
    '        return "shipped"\n'
    '    if state == "shipped":\n'
    '        if action == "refund":\n'
    '            return "refunded"\n'
    '        raise ValueError("bad action")\n'
    '    if action == "cancel" and can_cancel(state):\n'
    '        return "cancelled"\n'
    "    return state\n"
)
_o5_old = (
    "def can_cancel(state):\n"
    '    return state in ("new", "paid")\n'
)
_o5_new = (
    "def can_cancel(state):\n"
    '    return state in ("new", "paid")\n\n\n'
    "def available_actions(state):\n"
    '    if state in ("cancelled", "refunded"):\n'
    "        return []\n"
    '    if state == "new":\n'
    '        return ["pay", "cancel"]\n'
    '    if state == "paid":\n'
    '        return ["ship", "cancel"]\n'
    '    if state == "shipped":\n'
    '        return ["refund"]\n'
    "    return []\n"
)
T(
    id="ind_M03a",
    family="ind_med_state",
    type="state_machine_evolution",
    difficulty="medium",
    focus="订单状态机递进：ship→cancel→终端守卫→refund 改约→可用动作表",
    files={"order.py": _ord_a},
    steps=[
        {
            "instruction": (
                "order.py 新增转移：paid 状态下 action 为 ship 时应返回 shipped"
                "（当前该转移不存在）。"
            ),
            "tests": (
                "import order\n\n\n"
                "def test_ship():\n"
                '    assert order.advance("paid", "ship") == "shipped"\n\n\n'
                "def test_pay_regression():\n"
                '    assert order.advance("new", "pay") == "paid"\n\n\n'
                "def test_unknown_regression():\n"
                '    assert order.advance("new", "ship") == "new"\n'
            ),
            "ops": [("replace", "order.py", _o1_old, _o1_new)],
            "expect_targets": {"order.py"},
        },
        {
            "instruction": (
                "order.py 新增转移：action 为 cancel 且 can_cancel(state) "
                "为真时应返回 cancelled（当前无此转移）。"
            ),
            "tests": (
                "import order\n\n\n"
                "def test_cancel_new():\n"
                '    assert order.advance("new", "cancel") == "cancelled"\n\n\n'
                "def test_cancel_paid():\n"
                '    assert order.advance("paid", "cancel") == "cancelled"\n\n\n'
                "def test_ship_regression():\n"
                '    assert order.advance("paid", "ship") == "shipped"\n'
            ),
            "ops": [("replace", "order.py", _o2_old, _o2_new)],
            "expect_targets": {"order.py"},
        },
        {
            "instruction": (
                "请修改 order.py 中的 advance(state, action)："
                "shipped 或 cancelled 状态下任何 action 应抛出 ValueError"
                "（当前静默返回原状态）。"
            ),
            "tests": (
                "import pytest\n\n"
                "import order\n\n\n"
                "def test_terminal_raises():\n"
                "    with pytest.raises(ValueError):\n"
                '        order.advance("shipped", "pay")\n'
                "    with pytest.raises(ValueError):\n"
                '        order.advance("cancelled", "pay")\n\n\n'
                "def test_normal_regression():\n"
                '    assert order.advance("new", "pay") == "paid"\n'
            ),
            "ops": [("replace", "order.py", _o3_old, _o3_new)],
            "expect_targets": {"order.py"},
        },
        {
            "instruction": (
                "请修改 order.py 中的 advance(state, action)："
                "shipped 状态下 action 为 refund 时应返回 refunded"
                "（其他 shipped 上的非法 action 仍应抛 ValueError）。"
            ),
            "tests": (
                "import pytest\n\n"
                "import order\n\n\n"
                "def test_refund():\n"
                '    assert order.advance("shipped", "refund") == "refunded"\n\n\n'
                "def test_refunded_terminal():\n"
                "    with pytest.raises(ValueError):\n"
                '        order.advance("refunded", "pay")\n\n\n'
                "def test_shipped_bad_action():\n"
                "    with pytest.raises(ValueError):\n"
                '        order.advance("shipped", "pay")\n'
            ),
            "ops": [("replace", "order.py", _o4_old, _o4_new)],
            "expect_targets": {"order.py"},
        },
        {
            "instruction": (
                "order.py 新增 available_actions(state)：返回该状态下合法 "
                "action 列表，new→[pay, cancel]，paid→[ship, cancel]，"
                "shipped→[refund]，cancelled/refunded→[]。"
            ),
            "tests": (
                "import order\n\n\n"
                "def test_actions_new():\n"
                '    assert order.available_actions("new") == ["pay", "cancel"]\n\n\n'
                "def test_actions_shipped():\n"
                '    assert order.available_actions("shipped") == ["refund"]\n\n\n'
                "def test_actions_terminal():\n"
                '    assert order.available_actions("cancelled") == []\n'
                '    assert order.available_actions("refunded") == []\n\n\n'
                "def test_refund_regression():\n"
                '    assert order.advance("shipped", "refund") == "refunded"\n'
            ),
            "ops": [("replace", "order.py", _o5_old, _o5_new)],
            "expect_targets": {"order.py"},
        },
    ],
    info_points=[
        {"id": "ip_order_transitions", "type": "interface",
         "value": "new→paid→shipped→refunded；cancel 自 new/paid",
         "locator": "instruction:step1/2 + order.py",
         "needed_by_steps": [1, 2, 3, 4],
         "redundant_in_instruction": True},
        {"id": "ip_terminal_guard", "type": "implementation",
         "value": "cancelled/refunded 终态 raise ValueError",
         "locator": "instruction:step3/4 + order.py",
         "needed_by_steps": [3, 4, 5],
         "redundant_in_instruction": True},
        {"id": "ip_ship_refund_history", "type": "history",
         "value": "advance(\"shipped\",\"refund\")==\"refunded\"（step4 后保持）",
         "locator": "order.py (step4) + step5 回归 eval",
         "needed_by_steps": [5],
         "redundant_in_instruction": False},
        {"id": "ip_actions_table", "type": "interface",
         "value": "available_actions 各状态动作表",
         "locator": "instruction:step5 + order.py",
         "needed_by_steps": [5],
         "redundant_in_instruction": True},
    ],
)

# 变体 b：播放器状态机（play→pause/stop→finish 终端→buffering 改约→事件表）
_ply_b = (
    '"""Player states."""\n\n\n'
    "def on_event(state, event):\n"
    '    if state == "idle" and event == "play":\n'
    '        return "playing"\n'
    "    return state\n\n\n"
    "def is_playing(state):\n"
    '    return state == "playing"\n'
)
_p1_old = (
    "def on_event(state, event):\n"
    '    if state == "idle" and event == "play":\n'
    '        return "playing"\n'
    "    return state\n"
)
_p1_new = (
    "def on_event(state, event):\n"
    '    if state == "idle" and event == "play":\n'
    '        return "playing"\n'
    '    if state == "playing" and event == "pause":\n'
    '        return "paused"\n'
    '    if state == "paused" and event == "play":\n'
    '        return "playing"\n'
    "    return state\n"
)
_p2_old = (
    '    if state == "paused" and event == "play":\n'
    '        return "playing"\n'
    "    return state\n"
)
_p2_new = (
    '    if state == "paused" and event == "play":\n'
    '        return "playing"\n'
    '    if state in ("playing", "paused") and event == "stop":\n'
    '        return "idle"\n'
    "    return state\n"
)
_p3_old = (
    "def on_event(state, event):\n"
    '    if state == "idle" and event == "play":\n'
    '        return "playing"\n'
)
_p3_new = (
    "def on_event(state, event):\n"
    '    if state == "ended":\n'
    '        raise ValueError("ended")\n'
    '    if state == "idle" and event == "play":\n'
    '        return "playing"\n'
)
_p3b_old = (
    '    if state in ("playing", "paused") and event == "stop":\n'
    '        return "idle"\n'
    "    return state\n"
)
_p3b_new = (
    '    if state in ("playing", "paused") and event == "stop":\n'
    '        return "idle"\n'
    '    if state == "playing" and event == "finish":\n'
    '        return "ended"\n'
    "    return state\n"
)
_p4_old = (
    '    if state == "idle" and event == "play":\n'
    '        return "playing"\n'
    '    if state == "playing" and event == "pause":\n'
)
_p4_new = (
    '    if state == "idle" and event == "play":\n'
    '        return "buffering"\n'
    '    if state == "buffering" and event == "ready":\n'
    '        return "playing"\n'
    '    if state == "playing" and event == "pause":\n'
)
_p5_old = (
    "def is_playing(state):\n"
    '    return state == "playing"\n'
)
_p5_new = (
    "def is_playing(state):\n"
    '    return state == "playing"\n\n\n'
    "def available_events(state):\n"
    '    if state == "ended":\n'
    "        return []\n"
    '    if state == "idle":\n'
    '        return ["play"]\n'
    '    if state == "buffering":\n'
    '        return ["ready"]\n'
    '    if state == "playing":\n'
    '        return ["pause", "stop", "finish"]\n'
    '    if state == "paused":\n'
    '        return ["play", "stop"]\n'
    "    return []\n"
)
T(
    id="ind_M03b",
    family="ind_med_state",
    type="state_machine_evolution",
    difficulty="medium",
    focus="播放器状态机递进：pause/stop→finish 终端→buffering 改约→事件表",
    files={"player.py": _ply_b},
    steps=[
        {
            "instruction": (
                "player.py 新增转移：playing 下 pause 应返回 paused，"
                "paused 下 play 应回到 playing（当前两条转移都不存在）。"
            ),
            "tests": (
                "import player\n\n\n"
                "def test_pause():\n"
                '    assert player.on_event("playing", "pause") == "paused"\n\n\n'
                "def test_resume():\n"
                '    assert player.on_event("paused", "play") == "playing"\n\n\n'
                "def test_start_regression():\n"
                '    assert player.on_event("idle", "play") == "playing"\n'
            ),
            "ops": [("replace", "player.py", _p1_old, _p1_new)],
            "expect_targets": {"player.py"},
        },
        {
            "instruction": (
                "player.py 新增转移：playing 或 paused 下 stop 应返回 idle"
                "（当前无此转移）。"
            ),
            "tests": (
                "import player\n\n\n"
                "def test_stop_playing():\n"
                '    assert player.on_event("playing", "stop") == "idle"\n\n\n'
                "def test_stop_paused():\n"
                '    assert player.on_event("paused", "stop") == "idle"\n\n\n'
                "def test_pause_regression():\n"
                '    assert player.on_event("playing", "pause") == "paused"\n'
            ),
            "ops": [("replace", "player.py", _p2_old, _p2_new)],
            "expect_targets": {"player.py"},
        },
        {
            "instruction": (
                "请修改 player.py 中的 on_event(state, event)："
                "ended 状态下任何 event 应抛出 ValueError；"
                "playing 下 event 为 finish 时应返回 ended。"
            ),
            "tests": (
                "import pytest\n\n"
                "import player\n\n\n"
                "def test_finish():\n"
                '    assert player.on_event("playing", "finish") == "ended"\n\n\n'
                "def test_ended_terminal():\n"
                "    with pytest.raises(ValueError):\n"
                '        player.on_event("ended", "play")\n\n\n'
                "def test_stop_regression():\n"
                '    assert player.on_event("playing", "stop") == "idle"\n'
            ),
            "ops": [
                ("replace", "player.py", _p3_old, _p3_new),
                ("replace", "player.py", _p3b_old, _p3b_new),
            ],
            "expect_targets": {"player.py"},
        },
        {
            "instruction": (
                "请修改 player.py 中的 on_event(state, event)："
                "idle 下 play 应返回 buffering（不再是 playing），"
                "buffering 下 ready 应返回 playing。"
            ),
            "tests": (
                "import player\n\n\n"
                "def test_buffering():\n"
                '    assert player.on_event("idle", "play") == "buffering"\n\n\n'
                "def test_ready():\n"
                '    assert player.on_event("buffering", "ready") == "playing"\n\n\n'
                "def test_pause_regression():\n"
                '    assert player.on_event("playing", "pause") == "paused"\n\n\n'
                "def test_is_playing_regression():\n"
                '    assert player.is_playing("buffering") is False\n'
            ),
            "ops": [("replace", "player.py", _p4_old, _p4_new)],
            "expect_targets": {"player.py"},
        },
        {
            "instruction": (
                "player.py 新增 available_events(state)：返回该状态下合法 "
                "event 列表，idle→[play]，buffering→[ready]，"
                "playing→[pause, stop, finish]，paused→[play, stop]，"
                "ended→[]。"
            ),
            "tests": (
                "import player\n\n\n"
                "def test_events_playing():\n"
                '    assert player.available_events("playing") == [\n'
                '        "pause", "stop", "finish"]\n\n\n'
                "def test_events_ended():\n"
                '    assert player.available_events("ended") == []\n\n\n'
                "def test_buffering_regression():\n"
                '    assert player.on_event("idle", "play") == "buffering"\n'
            ),
            "ops": [("replace", "player.py", _p5_old, _p5_new)],
            "expect_targets": {"player.py"},
        },
    ],
    info_points=[
        {"id": "ip_player_transitions", "type": "interface",
         "value": "idle→buffering→playing⇄paused；stop→idle；finish→ended",
         "locator": "instruction:step1-4 + player.py",
         "needed_by_steps": [1, 2, 3, 4],
         "redundant_in_instruction": True},
        {"id": "ip_buffering_rework", "type": "implementation",
         "value": "idle+play→buffering，buffering+ready→playing",
         "locator": "instruction:step4 + player.py",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": True},
        {"id": "ip_finish_history", "type": "history",
         "value": "on_event(\"playing\",\"finish\")==\"ended\"（step3 后保持）",
         "locator": "player.py (step3) + step5 回归 eval",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": False},
        {"id": "ip_events_table", "type": "interface",
         "value": "available_events 各状态事件表",
         "locator": "instruction:step5 + player.py",
         "needed_by_steps": [5],
         "redundant_in_instruction": True},
    ],
)

# ============================================================ MF4 ind_med_cache
# 变体 a：Box 缓存（容量淘汰→命中统计→LRU→peek→禁存 None）
_box_a = (
    '"""Box cache."""\n\n\n'
    "class Box:\n"
    "    def __init__(self, cap):\n"
    "        self.cap = cap\n"
    "        self.data = {}\n\n"
    "    def put(self, k, v):\n"
    "        self.data[k] = v\n\n"
    "    def get(self, k):\n"
    "        return self.data.get(k)\n"
)
_b1_old = (
    "    def put(self, k, v):\n"
    "        self.data[k] = v\n"
)
_b1_new = (
    "    def put(self, k, v):\n"
    "        if k not in self.data and len(self.data) >= self.cap:\n"
    "            oldest = next(iter(self.data))\n"
    "            del self.data[oldest]\n"
    "        self.data[k] = v\n"
)
_b2_old = (
    "    def __init__(self, cap):\n"
    "        self.cap = cap\n"
    "        self.data = {}\n\n"
    "    def put(self, k, v):\n"
)
_b2_new = (
    "    def __init__(self, cap):\n"
    "        self.cap = cap\n"
    "        self.data = {}\n"
    "        self.hits = 0\n"
    "        self.misses = 0\n\n"
    "    def put(self, k, v):\n"
)
_b2g_old = (
    "    def get(self, k):\n"
    "        return self.data.get(k)\n"
)
_b2g_new = (
    "    def get(self, k):\n"
    "        if k in self.data:\n"
    "            self.hits += 1\n"
    "            return self.data[k]\n"
    "        self.misses += 1\n"
    "        return None\n"
)
_b3_old = (
    "    def get(self, k):\n"
    "        if k in self.data:\n"
    "            self.hits += 1\n"
    "            return self.data[k]\n"
    "        self.misses += 1\n"
    "        return None\n"
)
_b3_new = (
    "    def get(self, k):\n"
    "        if k in self.data:\n"
    "            v = self.data.pop(k)\n"
    "            self.data[k] = v\n"
    "            self.hits += 1\n"
    "            return v\n"
    "        self.misses += 1\n"
    "        return None\n"
)
_b3p_old = (
    "    def put(self, k, v):\n"
    "        if k not in self.data and len(self.data) >= self.cap:\n"
    "            oldest = next(iter(self.data))\n"
    "            del self.data[oldest]\n"
    "        self.data[k] = v\n"
)
_b3p_new = (
    "    def put(self, k, v):\n"
    "        if k in self.data:\n"
    "            del self.data[k]\n"
    "        elif len(self.data) >= self.cap:\n"
    "            oldest = next(iter(self.data))\n"
    "            del self.data[oldest]\n"
    "        self.data[k] = v\n"
)
_b4_old = (
    "    def get(self, k):\n"
    "        if k in self.data:\n"
    "            v = self.data.pop(k)\n"
    "            self.data[k] = v\n"
    "            self.hits += 1\n"
    "            return v\n"
    "        self.misses += 1\n"
    "        return None\n"
)
_b4_new = (
    "    def get(self, k):\n"
    "        if k in self.data:\n"
    "            v = self.data.pop(k)\n"
    "            self.data[k] = v\n"
    "            self.hits += 1\n"
    "            return v\n"
    "        self.misses += 1\n"
    "        return None\n\n"
    "    def peek(self, k):\n"
    "        return self.data.get(k)\n"
)
_b5_old = (
    "    def put(self, k, v):\n"
    "        if k in self.data:\n"
    "            del self.data[k]\n"
    "        elif len(self.data) >= self.cap:\n"
    "            oldest = next(iter(self.data))\n"
    "            del self.data[oldest]\n"
    "        self.data[k] = v\n"
)
_b5_new = (
    "    def put(self, k, v):\n"
    "        if v is None:\n"
    "            return\n"
    "        if k in self.data:\n"
    "            del self.data[k]\n"
    "        elif len(self.data) >= self.cap:\n"
    "            oldest = next(iter(self.data))\n"
    "            del self.data[oldest]\n"
    "        self.data[k] = v\n"
)
T(
    id="ind_M04a",
    family="ind_med_cache",
    type="cache_policy_evolution",
    difficulty="medium",
    focus="Box 缓存策略演进：容量淘汰→命中统计→LRU→peek→禁存 None",
    files={"box.py": _box_a},
    steps=[
        {
            "instruction": (
                "请修改 box.py 中 Box 的 put(k, v)："
                "写入新键且已满时应淘汰最早写入的键（当前无淘汰）。"
            ),
            "tests": (
                "import box\n\n\n"
                "def test_evict_oldest():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", 1)\n'
                '    c.put("b", 2)\n'
                '    c.put("c", 3)\n'
                '    assert c.get("a") is None\n'
                '    assert c.get("b") == 2\n'
                '    assert c.get("c") == 3\n\n\n'
                "def test_overwrite_no_evict():\n"
                "    c = box.Box(1)\n"
                '    c.put("a", 1)\n'
                '    c.put("a", 9)\n'
                '    assert c.get("a") == 9\n'
            ),
            "ops": [("replace", "box.py", _b1_old, _b1_new)],
            "expect_targets": {"box.py"},
        },
        {
            "instruction": (
                "box.py 的 Box 新增命中统计：get 命中时 hits 加 1，"
                "未命中时 misses 加 1（初始均为 0）。"
            ),
            "tests": (
                "import box\n\n\n"
                "def test_stats():\n"
                "    c = box.Box(3)\n"
                '    c.put("a", 1)\n'
                '    c.get("a")\n'
                '    c.get("z")\n'
                "    assert c.hits == 1\n"
                "    assert c.misses == 1\n\n\n"
                "def test_evict_regression():\n"
                "    c = box.Box(1)\n"
                '    c.put("a", 1)\n'
                '    c.put("b", 2)\n'
                '    assert c.get("a") is None\n'
                '    assert c.get("b") == 2\n'
            ),
            "ops": [
                ("replace", "box.py", _b2_old, _b2_new),
                ("replace", "box.py", _b2g_old, _b2g_new),
            ],
            "expect_targets": {"box.py"},
        },
        {
            "instruction": (
                "请修改 box.py 中 Box 的 get(k) 与 put(k, v)："
                "改为 LRU 语义——get 命中或覆盖写入都把该键移到最新，"
                "淘汰时丢最久未用的键（当前按写入顺序淘汰）。"
            ),
            "tests": (
                "import box\n\n\n"
                "def test_lru_get_refresh():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", 1)\n'
                '    c.put("b", 2)\n'
                '    c.get("a")\n'
                '    c.put("c", 3)\n'
                '    assert c.get("a") == 1\n'
                '    assert c.get("b") is None\n\n\n'
                "def test_lru_put_refresh():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", 1)\n'
                '    c.put("b", 2)\n'
                '    c.put("a", 9)\n'
                '    c.put("c", 3)\n'
                '    assert c.get("a") == 9\n'
                '    assert c.get("b") is None\n\n\n'
                "def test_stats_regression():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", 1)\n'
                '    c.get("a")\n'
                "    assert c.hits == 1\n"
            ),
            "ops": [
                ("replace", "box.py", _b3_old, _b3_new),
                ("replace", "box.py", _b3p_old, _b3p_new),
            ],
            "expect_targets": {"box.py"},
        },
        {
            "instruction": (
                "box.py 的 Box 新增 peek(k)：返回值但不计 hits/misses、"
                "不改变 LRU 顺序（与 get 区分）。"
            ),
            "tests": (
                "import box\n\n\n"
                "def test_peek_no_stats():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", 1)\n'
                '    assert c.peek("a") == 1\n'
                '    assert c.peek("z") is None\n'
                "    assert c.hits == 0\n"
                "    assert c.misses == 0\n\n\n"
                "def test_peek_no_order_change():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", 1)\n'
                '    c.put("b", 2)\n'
                '    c.peek("a")\n'
                '    c.put("c", 3)\n'
                '    assert c.get("a") is None\n'
                '    assert c.get("b") == 2\n\n\n'
                "def test_get_stats_regression():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", 1)\n'
                '    c.get("a")\n'
                "    assert c.hits == 1\n"
            ),
            "ops": [("replace", "box.py", _b4_old, _b4_new)],
            "expect_targets": {"box.py"},
        },
        {
            "instruction": (
                "请修改 box.py 中 Box 的 put(k, v)："
                "v 为 None 时应直接忽略不写入（当前会存入 None）。"
            ),
            "tests": (
                "import box\n\n\n"
                "def test_none_not_stored():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", None)\n'
                '    c.put("b", 1)\n'
                '    assert c.get("a") is None\n'
                "    assert c.misses == 1\n"
                "    assert c.hits == 0\n"
                '    c.put("a", 5)\n'
                '    assert c.get("a") == 5\n\n\n'
                "def test_peek_regression():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", 1)\n'
                '    assert c.peek("a") == 1\n'
                "    assert c.hits == 0\n\n\n"
                "def test_lru_regression():\n"
                "    c = box.Box(2)\n"
                '    c.put("a", 1)\n'
                '    c.put("b", 2)\n'
                '    c.get("a")\n'
                '    c.put("c", 3)\n'
                '    assert c.get("a") == 1\n'
            ),
            "ops": [("replace", "box.py", _b5_old, _b5_new)],
            "expect_targets": {"box.py"},
        },
    ],
    info_points=[
        {"id": "ip_evict_policy", "type": "implementation",
         "value": "满时淘汰最旧键（step1 写入序 → step3 LRU）",
         "locator": "instruction:step1/3 + box.py",
         "needed_by_steps": [1, 3],
         "redundant_in_instruction": True},
        {"id": "ip_stats_fields", "type": "interface",
         "value": "hits/misses 仅在 get 增计",
         "locator": "instruction:step2 + box.py",
         "needed_by_steps": [2, 4, 5],
         "redundant_in_instruction": True},
        {"id": "ip_lru_history", "type": "history",
         "value": "LRU 顺序在 step4 peek 加入后仍由 get/put 维护",
         "locator": "box.py (step3) + step4 回归 eval",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": False},
        {"id": "ip_none_rule", "type": "implementation",
         "value": "put(k, None) 忽略不写入",
         "locator": "instruction:step5 + box.py",
         "needed_by_steps": [5],
         "redundant_in_instruction": True},
    ],
)

# 变体 b：Shelf 货架缓存（列表结构：淘汰→统计→LRU→peek→禁存 None）
_shf_b = (
    '"""Shelf cache."""\n\n\n'
    "class Shelf:\n"
    "    def __init__(self, slots):\n"
    "        self.slots = slots\n"
    "        self.entries = []\n\n"
    "    def store(self, tag, val):\n"
    "        self.entries.append((tag, val))\n\n"
    "    def fetch(self, tag):\n"
    "        for t, v in reversed(self.entries):\n"
    "            if t == tag:\n"
    "                return v\n"
    "        return None\n"
)
_h1_old = (
    "    def store(self, tag, val):\n"
    "        self.entries.append((tag, val))\n"
)
_h1_new = (
    "    def store(self, tag, val):\n"
    "        self.entries = [(t, v) for t, v in self.entries if t != tag]\n"
    "        if len(self.entries) >= self.slots:\n"
    "            self.entries.pop(0)\n"
    "        self.entries.append((tag, val))\n"
)
_h2_old = (
    "    def __init__(self, slots):\n"
    "        self.slots = slots\n"
    "        self.entries = []\n\n"
    "    def store(self, tag, val):\n"
)
_h2_new = (
    "    def __init__(self, slots):\n"
    "        self.slots = slots\n"
    "        self.entries = []\n"
    "        self.hits = 0\n"
    "        self.misses = 0\n\n"
    "    def store(self, tag, val):\n"
)
_h2f_old = (
    "    def fetch(self, tag):\n"
    "        for t, v in reversed(self.entries):\n"
    "            if t == tag:\n"
    "                return v\n"
    "        return None\n"
)
_h2f_new = (
    "    def fetch(self, tag):\n"
    "        for t, v in reversed(self.entries):\n"
    "            if t == tag:\n"
    "                self.hits += 1\n"
    "                return v\n"
    "        self.misses += 1\n"
    "        return None\n"
)
_h3_old = (
    "    def fetch(self, tag):\n"
    "        for t, v in reversed(self.entries):\n"
    "            if t == tag:\n"
    "                self.hits += 1\n"
    "                return v\n"
    "        self.misses += 1\n"
    "        return None\n"
)
_h3_new = (
    "    def fetch(self, tag):\n"
    "        for i in range(len(self.entries) - 1, -1, -1):\n"
    "            if self.entries[i][0] == tag:\n"
    "                t, v = self.entries.pop(i)\n"
    "                self.entries.append((t, v))\n"
    "                self.hits += 1\n"
    "                return v\n"
    "        self.misses += 1\n"
    "        return None\n"
)
_h4_old = (
    "    def fetch(self, tag):\n"
    "        for i in range(len(self.entries) - 1, -1, -1):\n"
    "            if self.entries[i][0] == tag:\n"
    "                t, v = self.entries.pop(i)\n"
    "                self.entries.append((t, v))\n"
    "                self.hits += 1\n"
    "                return v\n"
    "        self.misses += 1\n"
    "        return None\n"
)
_h4_new = (
    "    def fetch(self, tag):\n"
    "        for i in range(len(self.entries) - 1, -1, -1):\n"
    "            if self.entries[i][0] == tag:\n"
    "                t, v = self.entries.pop(i)\n"
    "                self.entries.append((t, v))\n"
    "                self.hits += 1\n"
    "                return v\n"
    "        self.misses += 1\n"
    "        return None\n\n"
    "    def peek(self, tag):\n"
    "        for t, v in reversed(self.entries):\n"
    "            if t == tag:\n"
    "                return v\n"
    "        return None\n"
)
_h5_old = (
    "    def store(self, tag, val):\n"
    "        self.entries = [(t, v) for t, v in self.entries if t != tag]\n"
    "        if len(self.entries) >= self.slots:\n"
    "            self.entries.pop(0)\n"
    "        self.entries.append((tag, val))\n"
)
_h5_new = (
    "    def store(self, tag, val):\n"
    "        if val is None:\n"
    "            return\n"
    "        self.entries = [(t, v) for t, v in self.entries if t != tag]\n"
    "        if len(self.entries) >= self.slots:\n"
    "            self.entries.pop(0)\n"
    "        self.entries.append((tag, val))\n"
)
T(
    id="ind_M04b",
    family="ind_med_cache",
    type="cache_policy_evolution",
    difficulty="medium",
    focus="Shelf 货架缓存演进：容量淘汰→统计→LRU→peek→禁存 None（列表结构）",
    files={"shelf.py": _shf_b},
    steps=[
        {
            "instruction": (
                "请修改 shelf.py 中 Shelf 的 store(tag, val)："
                "同 tag 覆盖旧值；写入新 tag 且已满时淘汰最早条目。"
            ),
            "tests": (
                "import shelf\n\n\n"
                "def test_store_evict():\n"
                "    s = shelf.Shelf(2)\n"
                '    s.store("a", 1)\n'
                '    s.store("b", 2)\n'
                '    s.store("c", 3)\n'
                '    assert s.fetch("a") is None\n'
                '    assert s.fetch("b") == 2\n'
                '    assert s.fetch("c") == 3\n\n\n'
                "def test_store_overwrite():\n"
                "    s = shelf.Shelf(2)\n"
                '    s.store("a", 1)\n'
                '    s.store("a", 9)\n'
                '    assert s.fetch("a") == 9\n'
                "    assert len(s.entries) == 1\n"
            ),
            "ops": [("replace", "shelf.py", _h1_old, _h1_new)],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "shelf.py 的 Shelf 新增命中统计：fetch 命中时 hits 加 1，"
                "未命中时 misses 加 1（初始均为 0）。"
            ),
            "tests": (
                "import shelf\n\n\n"
                "def test_stats():\n"
                "    s = shelf.Shelf(3)\n"
                '    s.store("a", 1)\n'
                '    s.fetch("a")\n'
                '    s.fetch("z")\n'
                "    assert s.hits == 1\n"
                "    assert s.misses == 1\n\n\n"
                "def test_store_regression():\n"
                "    s = shelf.Shelf(1)\n"
                '    s.store("a", 1)\n'
                '    s.store("b", 2)\n'
                '    assert s.fetch("a") is None\n'
                '    assert s.fetch("b") == 2\n'
            ),
            "ops": [
                ("replace", "shelf.py", _h2_old, _h2_new),
                ("replace", "shelf.py", _h2f_old, _h2f_new),
            ],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "请修改 shelf.py 中 Shelf 的 fetch(tag)："
                "命中时把该条目移到列表末尾（最近使用），"
                "淘汰仍丢最前端条目（当前命中不改变顺序）。"
            ),
            "tests": (
                "import shelf\n\n\n"
                "def test_lru_fetch_moves_to_end():\n"
                "    s = shelf.Shelf(2)\n"
                '    s.store("a", 1)\n'
                '    s.store("b", 2)\n'
                '    s.fetch("a")\n'
                '    s.store("c", 3)\n'
                '    assert s.fetch("a") == 1\n'
                '    assert s.fetch("b") is None\n\n\n'
                "def test_stats_regression():\n"
                "    s = shelf.Shelf(2)\n"
                '    s.store("a", 1)\n'
                '    s.fetch("a")\n'
                "    assert s.hits == 1\n"
                '    assert s.fetch("z") is None\n'
                "    assert s.misses == 1\n"
            ),
            "ops": [("replace", "shelf.py", _h3_old, _h3_new)],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "shelf.py 的 Shelf 新增 peek(tag)：返回值但不计 hits/misses、"
                "不把条目移到末尾（与 fetch 区分）。"
            ),
            "tests": (
                "import shelf\n\n\n"
                "def test_peek_quiet():\n"
                "    s = shelf.Shelf(2)\n"
                '    s.store("a", 1)\n'
                '    s.store("b", 2)\n'
                '    assert s.peek("a") == 1\n'
                '    assert s.peek("z") is None\n'
                "    assert s.hits == 0\n"
                "    assert s.misses == 0\n"
                '    assert s.entries[0][0] == "a"\n\n\n'
                "def test_fetch_still_lru():\n"
                "    s = shelf.Shelf(2)\n"
                '    s.store("a", 1)\n'
                '    s.store("b", 2)\n'
                '    s.fetch("a")\n'
                '    s.store("c", 3)\n'
                '    assert s.fetch("a") == 1\n'
            ),
            "ops": [("replace", "shelf.py", _h4_old, _h4_new)],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "请修改 shelf.py 中 Shelf 的 store(tag, val)："
                "val 为 None 时应直接忽略不写入（当前会存入 None）。"
            ),
            "tests": (
                "import shelf\n\n\n"
                "def test_none_ignored():\n"
                "    s = shelf.Shelf(2)\n"
                '    s.store("a", None)\n'
                '    assert s.entries == []\n'
                '    s.store("a", 5)\n'
                '    assert s.fetch("a") == 5\n\n\n'
                "def test_peek_regression():\n"
                "    s = shelf.Shelf(2)\n"
                '    s.store("a", 1)\n'
                '    assert s.peek("a") == 1\n'
                "    assert s.hits == 0\n\n\n"
                "def test_lru_regression():\n"
                "    s = shelf.Shelf(2)\n"
                '    s.store("a", 1)\n'
                '    s.store("b", 2)\n'
                '    s.fetch("a")\n'
                '    s.store("c", 3)\n'
                '    assert s.fetch("a") == 1\n'
            ),
            "ops": [("replace", "shelf.py", _h5_old, _h5_new)],
            "expect_targets": {"shelf.py"},
        },
    ],
    info_points=[
        {"id": "ip_store_evict", "type": "implementation",
         "value": "store 覆盖同 tag；满时 pop(0) 淘汰最旧",
         "locator": "instruction:step1 + shelf.py",
         "needed_by_steps": [1, 3],
         "redundant_in_instruction": True},
        {"id": "ip_fetch_stats", "type": "interface",
         "value": "fetch 命中/未命中增计 hits/misses",
         "locator": "instruction:step2 + shelf.py",
         "needed_by_steps": [2, 4],
         "redundant_in_instruction": True},
        {"id": "ip_lru_move_history", "type": "history",
         "value": "fetch 命中移到 entries 末尾（step3 后保持）",
         "locator": "shelf.py (step3) + step4 回归 eval",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": False},
        {"id": "ip_none_ignored", "type": "implementation",
         "value": "store(tag, None) 忽略",
         "locator": "instruction:step5 + shelf.py",
         "needed_by_steps": [5],
         "redundant_in_instruction": True},
    ],
)

# ============================================================ MF5 ind_med_hierarchy
# 变体 a：图形类层级（新增 Circle → label 格式 → 新增 Triangle → 基类默认 → Square 继承 Rect）
_shp_a = (
    '"""Shapes."""\n\n\n'
    "class Shape:\n"
    "    def area(self):\n"
    "        return 0\n\n"
    "    def label(self):\n"
    '        return "shape"\n\n\n'
    "class Rect(Shape):\n"
    "    def __init__(self, w, h):\n"
    "        self.w = w\n"
    "        self.h = h\n\n"
    "    def area(self):\n"
    "        return self.w * self.h\n\n"
    "    def label(self):\n"
    '        return "rect"\n'
)
_h1_old = (
    '    def label(self):\n'
    '        return "rect"\n'
)
_h1_new = (
    '    def label(self):\n'
    '        return "rect"\n\n\n'
    "class Circle(Shape):\n"
    "    def __init__(self, r):\n"
    "        self.r = r\n\n"
    "    def area(self):\n"
    "        return 3.14 * self.r * self.r\n\n"
    "    def label(self):\n"
    '        return "circle"\n'
)
_h2_shape_old = (
    "class Shape:\n"
    "    def area(self):\n"
    "        return 0\n\n"
    "    def label(self):\n"
    '        return "shape"\n'
)
_h2_shape_new = (
    "class Shape:\n"
    "    def area(self):\n"
    "        return 0\n\n"
    "    def label(self):\n"
    '        return "shape#0"\n'
)
_h2_rect_old = (
    "    def label(self):\n"
    '        return "rect"\n'
)
_h2_rect_new = (
    "    def label(self):\n"
    '        return f"rect#{self.area()}"\n'
)
_h2_circ_old = (
    "    def label(self):\n"
    '        return "circle"\n'
)
_h2_circ_new = (
    "    def label(self):\n"
    '        return f"circle#{self.area()}"\n'
)
_h3_old = (
    "    def label(self):\n"
    '        return f"circle#{self.area()}"\n'
)
_h3_new = (
    "    def label(self):\n"
    '        return f"circle#{self.area()}"\n\n\n'
    "class Triangle(Shape):\n"
    "    def __init__(self, base, height):\n"
    "        self.base = base\n"
    "        self.height = height\n\n"
    "    def area(self):\n"
    "        return self.base * self.height / 2\n\n"
    "    def label(self):\n"
    '        return f"triangle#{self.area()}"\n'
)
_h4_shape_old = (
    "class Shape:\n"
    "    def area(self):\n"
    "        return 0\n\n"
    "    def label(self):\n"
    '        return "shape#0"\n'
)
_h4_shape_new = (
    "class Shape:\n"
    "    def area(self):\n"
    '        raise NotImplementedError("area")\n\n'
    "    def label(self):\n"
    '        return "shape#na"\n'
)
_h5_old = (
    "    def label(self):\n"
    '        return f"triangle#{self.area()}"\n'
)
_h5_new = (
    "    def label(self):\n"
    '        return f"triangle#{self.area()}"\n\n\n'
    "class Square(Rect):\n"
    "    def __init__(self, side):\n"
    "        super().__init__(side, side)\n"
)
T(
    id="ind_M05a",
    family="ind_med_hierarchy",
    type="class_hierarchy_evolution",
    difficulty="medium",
    focus="图形类层级演进：新增 Circle→label 格式→Triangle→基类默认改约→Square 继承 Rect",
    files={"shapes.py": _shp_a},
    steps=[
        {
            "instruction": (
                "shapes.py 新增子类 Circle(Shape)：构造参数 r，"
                "area 返回 3.14 * r * r，label 返回 \"circle\"。"
            ),
            "tests": (
                "import shapes\n\n\n"
                "def test_circle_area():\n"
                "    c = shapes.Circle(2)\n"
                "    assert abs(c.area() - 12.56) < 1e-9\n"
                '    assert c.label() == "circle"\n\n\n'
                "def test_is_shape():\n"
                "    assert isinstance(shapes.Circle(1), shapes.Shape)\n\n\n"
                "def test_rect_regression():\n"
                "    r = shapes.Rect(3, 4)\n"
                "    assert r.area() == 12\n"
                '    assert r.label() == "rect"\n'
            ),
            "ops": [("replace", "shapes.py", _h1_old, _h1_new)],
            "expect_targets": {"shapes.py"},
        },
        {
            "instruction": (
                "请修改 shapes.py 中的 label() 格式："
                "所有已有类的 label 应返回 名称#面积"
                "（如 rect#12、circle#12.56、shape#0）。"
            ),
            "tests": (
                "import shapes\n\n\n"
                "def test_rect_label():\n"
                '    assert shapes.Rect(3, 4).label() == "rect#12"\n\n\n'
                "def test_circle_label():\n"
                '    assert shapes.Circle(2).label() == "circle#12.56"\n\n\n'
                "def test_base_label():\n"
                '    assert shapes.Shape().label() == "shape#0"\n\n\n'
                "def test_area_regression():\n"
                "    assert shapes.Rect(2, 5).area() == 10\n"
            ),
            "ops": [
                ("replace", "shapes.py", _h2_shape_old, _h2_shape_new),
                ("replace", "shapes.py", _h2_rect_old, _h2_rect_new),
                ("replace", "shapes.py", _h2_circ_old, _h2_circ_new),
            ],
            "expect_targets": {"shapes.py"},
        },
        {
            "instruction": (
                "shapes.py 新增子类 Triangle(Shape)：构造参数 base、height，"
                "area 返回 base * height / 2，label 遵循 名称#面积 格式。"
            ),
            "tests": (
                "import shapes\n\n\n"
                "def test_triangle():\n"
                "    t = shapes.Triangle(6, 4)\n"
                "    assert t.area() == 12\n"
                '    assert t.label() == "triangle#12.0"\n\n\n'
                "def test_is_shape():\n"
                "    assert isinstance(shapes.Triangle(1, 1), shapes.Shape)\n\n\n"
                "def test_label_format_regression():\n"
                '    assert shapes.Rect(3, 4).label() == "rect#12"\n'
            ),
            "ops": [("replace", "shapes.py", _h3_old, _h3_new)],
            "expect_targets": {"shapes.py"},
        },
        {
            "instruction": (
                "请修改 shapes.py 中 Shape 的基类默认："
                "area 应抛出 NotImplementedError，"
                "label 应返回 \"shape#na\"（子类已覆盖的行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import shapes\n\n\n"
                "def test_base_area_raises():\n"
                "    with pytest.raises(NotImplementedError):\n"
                "        shapes.Shape().area()\n\n\n"
                "def test_base_label():\n"
                '    assert shapes.Shape().label() == "shape#na"\n\n\n'
                "def test_subclass_still_works():\n"
                "    assert shapes.Rect(3, 4).area() == 12\n"
                '    assert shapes.Triangle(6, 4).label() == "triangle#12.0"\n'
            ),
            "ops": [("replace", "shapes.py", _h4_shape_old, _h4_shape_new)],
            "expect_targets": {"shapes.py"},
        },
        {
            "instruction": (
                "shapes.py 新增子类 Square(Rect)：构造参数 side，"
                "通过 super 调用 Rect.__init__(side, side)（area/label 继承 Rect）。"
            ),
            "tests": (
                "import shapes\n\n\n"
                "def test_square():\n"
                "    s = shapes.Square(5)\n"
                "    assert s.area() == 25\n"
                '    assert s.label() == "rect#25"\n'
                "    assert isinstance(s, shapes.Rect)\n\n\n"
                "def test_base_default_regression():\n"
                "    import pytest\n"
                "    with pytest.raises(NotImplementedError):\n"
                "        shapes.Shape().area()\n\n\n"
                "def test_triangle_regression():\n"
                "    assert shapes.Triangle(6, 4).area() == 12\n"
            ),
            "ops": [("replace", "shapes.py", _h5_old, _h5_new)],
            "expect_targets": {"shapes.py"},
        },
    ],
    info_points=[
        {"id": "ip_circle_ctor", "type": "interface",
         "value": "Circle(r)：area=3.14*r*r，label 含面积",
         "locator": "instruction:step1 + shapes.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_label_format", "type": "implementation",
         "value": "label = 名称#面积",
         "locator": "instruction:step2 + shapes.py",
         "needed_by_steps": [2, 3, 5],
         "redundant_in_instruction": True},
        {"id": "ip_base_default", "type": "implementation",
         "value": "Shape.area 抛 NotImplementedError；label=shape#na",
         "locator": "instruction:step4 + shapes.py",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": True},
        {"id": "ip_rect_history", "type": "history",
         "value": "Rect(3,4).area()==12 且 label==rect#12（step2-4 后保持）",
         "locator": "shapes.py (step2) + step5 回归 eval",
         "needed_by_steps": [3, 4, 5],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：文档块层级（新增 Image → envelope 标签格式 → 新增 Quote → 基类默认 → Heading 继承 Para）
_blk_b = (
    '"""Document blocks."""\n\n\n'
    "class Block:\n"
    "    def render(self):\n"
    '        return ""\n\n'
    "    def kind(self):\n"
    '        return "block"\n\n\n'
    "class Para(Block):\n"
    "    def __init__(self, text):\n"
    "        self.text = text\n\n"
    "    def render(self):\n"
    "        return self.text\n\n"
    "    def kind(self):\n"
    '        return "para"\n'
)
_k1_old = (
    "    def kind(self):\n"
    '        return "para"\n'
)
_k1_new = (
    "    def kind(self):\n"
    '        return "para"\n\n\n'
    "class Image(Block):\n"
    "    def __init__(self, src):\n"
    "        self.src = src\n\n"
    "    def render(self):\n"
    '        return f"[img:{self.src}]"\n\n'
    "    def kind(self):\n"
    '        return "image"\n'
)
_k2_block_old = (
    "class Block:\n"
    "    def render(self):\n"
    '        return ""\n\n'
    "    def kind(self):\n"
    '        return "block"\n'
)
_k2_block_new = (
    "class Block:\n"
    "    def render(self):\n"
    '        return ""\n\n'
    "    def kind(self):\n"
    '        return "block"\n\n'
    "    def envelope(self):\n"
    '        return f"<{self.kind()}>{self.render()}</{self.kind()}>"\n'
)
_k2_para_old = (
    "    def kind(self):\n"
    '        return "para"\n'
)
_k2_para_new = (
    "    def kind(self):\n"
    '        return "para"\n\n'
    "    def envelope(self):\n"
    '        return f"<para>{self.text}</para>"\n'
)
_k2_img_old = (
    "    def kind(self):\n"
    '        return "image"\n'
)
_k2_img_new = (
    "    def kind(self):\n"
    '        return "image"\n\n'
    "    def envelope(self):\n"
    '        return f"<image>{self.src}</image>"\n'
)
_k3_old = (
    "    def envelope(self):\n"
    '        return f"<image>{self.src}</image>"\n'
)
_k3_new = (
    "    def envelope(self):\n"
    '        return f"<image>{self.src}</image>"\n\n\n'
    "class Quote(Block):\n"
    "    def __init__(self, text):\n"
    "        self.text = text\n\n"
    "    def render(self):\n"
    '        return f"> {self.text}"\n\n'
    "    def kind(self):\n"
    '        return "quote"\n'
)
_k4_block_old = (
    "class Block:\n"
    "    def render(self):\n"
    '        return ""\n\n'
    "    def kind(self):\n"
    '        return "block"\n\n'
    "    def envelope(self):\n"
    '        return f"<{self.kind()}>{self.render()}</{self.kind()}>"\n'
)
_k4_block_new = (
    "class Block:\n"
    "    def render(self):\n"
    '        return ""\n\n'
    "    def kind(self):\n"
    '        return "block"\n\n'
    "    def envelope(self):\n"
    '        return f"<{self.kind()}>{self.render()}</{self.kind()}>"\n\n'
    "    def plain(self):\n"
    '        return self.render().strip()\n'
)
_k5_old = (
    "    def kind(self):\n"
    '        return "quote"\n'
)
_k5_new = (
    "    def kind(self):\n"
    '        return "quote"\n\n\n'
    "class Heading(Para):\n"
    "    def __init__(self, text, level=1):\n"
    "        super().__init__(text)\n"
    "        self.level = level\n\n"
    "    def render(self):\n"
    '        return f"{self.level}. {self.text}"\n'
)
T(
    id="ind_M05b",
    family="ind_med_hierarchy",
    type="class_hierarchy_evolution",
    difficulty="medium",
    focus="文档块层级演进：新增 Image→envelope 格式→Quote→基类默认 plain→Heading 继承 Para",
    files={"blocks.py": _blk_b},
    steps=[
        {
            "instruction": (
                "blocks.py 新增子类 Image(Block)：构造参数 src，"
                "render 返回 [img:src] 形式，kind 返回 \"image\"。"
            ),
            "tests": (
                "import blocks\n\n\n"
                "def test_image():\n"
                "    im = blocks.Image(\"pic.png\")\n"
                '    assert im.render() == "[img:pic.png]"\n'
                '    assert im.kind() == "image"\n'
                "    assert isinstance(im, blocks.Block)\n\n\n"
                "def test_para_regression():\n"
                '    p = blocks.Para("hi")\n'
                '    assert p.render() == "hi"\n'
                '    assert p.kind() == "para"\n'
            ),
            "ops": [("replace", "blocks.py", _k1_old, _k1_new)],
            "expect_targets": {"blocks.py"},
        },
        {
            "instruction": (
                "blocks.py 的 Block 新增 envelope() 默认实现，"
                "返回 <kind>render</kind> 形式；"
                "Para 与 Image 各自覆盖为 <para>text</para> 与 <image>src</image>。"
            ),
            "tests": (
                "import blocks\n\n\n"
                "def test_para_envelope():\n"
                '    assert blocks.Para("hi").envelope() == "<para>hi</para>"\n\n\n'
                "def test_image_envelope():\n"
                '    assert blocks.Image("a.png").envelope() == "<image>a.png</image>"\n\n\n'
                "def test_base_envelope():\n"
                '    assert blocks.Block().envelope() == "<block></block>"\n\n\n'
                "def test_kind_regression():\n"
                '    assert blocks.Image("x").kind() == "image"\n'
            ),
            "ops": [
                ("replace", "blocks.py", _k2_block_old, _k2_block_new),
                ("replace", "blocks.py", _k2_para_old, _k2_para_new),
                ("replace", "blocks.py", _k2_img_old, _k2_img_new),
            ],
            "expect_targets": {"blocks.py"},
        },
        {
            "instruction": (
                "blocks.py 新增子类 Quote(Block)：构造参数 text，"
                "render 返回 > 前缀引用形式，kind 返回 \"quote\"。"
            ),
            "tests": (
                "import blocks\n\n\n"
                "def test_quote():\n"
                '    q = blocks.Quote("note")\n'
                '    assert q.render() == "> note"\n'
                '    assert q.kind() == "quote"\n\n\n'
                "def test_envelope_regression():\n"
                '    assert blocks.Para("hi").envelope() == "<para>hi</para>"\n\n\n'
                "def test_image_regression():\n"
                '    assert blocks.Image("a.png").kind() == "image"\n'
            ),
            "ops": [("replace", "blocks.py", _k3_old, _k3_new)],
            "expect_targets": {"blocks.py"},
        },
        {
            "instruction": (
                "请修改 blocks.py 中 Block 的基类默认："
                "新增 plain() 方法，返回 render 结果去掉首尾空白"
                "（子类未覆盖，全部继承该默认）。"
            ),
            "tests": (
                "import blocks\n\n\n"
                "def test_base_plain():\n"
                '    assert blocks.Block().plain() == ""\n\n\n'
                "def test_para_plain_inherited():\n"
                '    assert blocks.Para("  hi  ").plain() == "hi"\n\n\n'
                "def test_quote_plain_inherited():\n"
                '    assert blocks.Quote("  x ").plain() == ">   x"\n\n\n'
                "def test_envelope_regression():\n"
                '    assert blocks.Para("hi").envelope() == "<para>hi</para>"\n'
            ),
            "ops": [("replace", "blocks.py", _k4_block_old, _k4_block_new)],
            "expect_targets": {"blocks.py"},
        },
        {
            "instruction": (
                "blocks.py 新增子类 Heading(Para)：构造参数 text、level"
                "（默认 1），render 返回 \"level. text\" 形式"
                "（envelope/plain 继承既有实现）。"
            ),
            "tests": (
                "import blocks\n\n\n"
                "def test_heading():\n"
                '    h = blocks.Heading("Title", 2)\n'
                '    assert h.render() == "2. Title"\n'
                '    assert h.kind() == "para"\n'
                "    assert isinstance(h, blocks.Para)\n\n\n"
                "def test_heading_default_level():\n"
                '    assert blocks.Heading("T").render() == "1. T"\n\n\n'
                "def test_plain_regression():\n"
                '    assert blocks.Para("  hi  ").plain() == "hi"\n'
            ),
            "ops": [("replace", "blocks.py", _k5_old, _k5_new)],
            "expect_targets": {"blocks.py"},
        },
    ],
    info_points=[
        {"id": "ip_image_ctor", "type": "interface",
         "value": "Image(src)：render=[img:src]，kind=image",
         "locator": "instruction:step1 + blocks.py",
         "needed_by_steps": [1, 2],
         "redundant_in_instruction": True},
        {"id": "ip_envelope_format", "type": "implementation",
         "value": "envelope=<kind>render</kind>，Para/Image 覆盖",
         "locator": "instruction:step2 + blocks.py",
         "needed_by_steps": [2, 3, 5],
         "redundant_in_instruction": True},
        {"id": "ip_plain_default", "type": "implementation",
         "value": "Block.plain() strip(render())，子类继承",
         "locator": "instruction:step4 + blocks.py",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": True},
        {"id": "ip_para_history", "type": "history",
         "value": "Para(hi).envelope()==<para>hi</para>（step2 后保持）",
         "locator": "blocks.py (step2) + step5 回归 eval",
         "needed_by_steps": [3, 4, 5],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ MF6 ind_med_parser
# 变体 a：表达式解析（tokenizer 分离运算符→加法→减法→多位数→乘法）
_expr_a = (
    '"""Expression parser."""\n\n\n'
    "def tokenize(s):\n"
    "    return s.split()\n\n\n"
    "def evaluate(s):\n"
    "    for t in tokenize(s):\n"
    "        if t.isdigit():\n"
    "            return int(t)\n"
    "    return 0\n"
)
_t1_old = (
    "def tokenize(s):\n"
    "    return s.split()\n"
)
_t1_new = (
    "def tokenize(s):\n"
    "    out = []\n"
    "    for ch in s:\n"
    '        if ch in "+-*/":\n'
    "            out.append(ch)\n"
    "        elif not ch.isspace():\n"
    "            out.append(ch)\n"
    "    return out\n"
)
_e2_old = (
    "def evaluate(s):\n"
    "    for t in tokenize(s):\n"
    "        if t.isdigit():\n"
    "            return int(t)\n"
    "    return 0\n"
)
_e2_new = (
    "def evaluate(s):\n"
    "    toks = tokenize(s)\n"
    "    total = int(toks[0])\n"
    "    i = 1\n"
    "    while i < len(toks):\n"
    '        if toks[i] == "+":\n'
    "            total = total + int(toks[i + 1])\n"
    "        i += 2\n"
    "    return total\n"
)
_e3_old = (
    '        if toks[i] == "+":\n'
    "            total = total + int(toks[i + 1])\n"
)
_e3_new = (
    '        if toks[i] == "+":\n'
    "            total = total + int(toks[i + 1])\n"
    '        elif toks[i] == "-":\n'
    "            total = total - int(toks[i + 1])\n"
)
_t4_old = (
    "def tokenize(s):\n"
    "    out = []\n"
    "    for ch in s:\n"
    '        if ch in "+-*/":\n'
    "            out.append(ch)\n"
    "        elif not ch.isspace():\n"
    "            out.append(ch)\n"
    "    return out\n"
)
_t4_new = (
    "def tokenize(s):\n"
    "    out = []\n"
    '    buf = ""\n'
    "    for ch in s:\n"
    '        if ch in "+-*/":\n'
    "            if buf:\n"
    "                out.append(buf)\n"
    '                buf = ""\n'
    "            out.append(ch)\n"
    "        elif ch.isspace():\n"
    "            if buf:\n"
    "                out.append(buf)\n"
    '                buf = ""\n'
    "        else:\n"
    '            buf += ch\n'
    "    if buf:\n"
    "        out.append(buf)\n"
    "    return out\n"
)
_e5_old = (
    '        if toks[i] == "+":\n'
    "            total = total + int(toks[i + 1])\n"
    '        elif toks[i] == "-":\n'
    "            total = total - int(toks[i + 1])\n"
)
_e5_new = (
    '        if toks[i] == "+":\n'
    "            total = total + int(toks[i + 1])\n"
    '        elif toks[i] == "-":\n'
    "            total = total - int(toks[i + 1])\n"
    '        elif toks[i] == "*":\n'
    "            total = total * int(toks[i + 1])\n"
)
T(
    id="ind_M06a",
    family="ind_med_parser",
    type="grammar_incremental",
    difficulty="medium",
    focus="表达式解析文法增量：tokenizer 分离运算符→加法→减法→多位数→乘法",
    files={"expr.py": _expr_a},
    steps=[
        {
            "instruction": (
                "请修改 expr.py 中的 tokenize(s)："
                "应把 + - * / 从操作数中分离为独立 token"
                "（当前按空白 split，\"1+2\" 得到单个 token）。"
            ),
            "tests": (
                "import expr\n\n\n"
                "def test_split_ops():\n"
                '    assert expr.tokenize("1+2") == ["1", "+", "2"]\n'
                '    assert expr.tokenize("3-4") == ["3", "-", "4"]\n\n\n'
                "def test_spaced_still_works():\n"
                '    assert expr.tokenize("1 + 2") == ["1", "+", "2"]\n\n\n'
                "def test_evaluate_regression():\n"
                '    assert expr.evaluate("1 2 3") == 1\n'
            ),
            "ops": [("replace", "expr.py", _t1_old, _t1_new)],
            "expect_targets": {"expr.py"},
        },
        {
            "instruction": (
                "请修改 expr.py 中的 evaluate(s)："
                "应按从左到右只处理 + 运算符求值"
                "（当前把所有数字直接相加、忽略运算符）。"
            ),
            "tests": (
                "import expr\n\n\n"
                "def test_add():\n"
                '    assert expr.evaluate("1+2") == 3\n'
                '    assert expr.evaluate("5 + 4") == 9\n\n\n'
                "def test_single_number():\n"
                '    assert expr.evaluate("7") == 7\n\n\n'
                "def test_tokenize_regression():\n"
                '    assert expr.tokenize("1+2") == ["1", "+", "2"]\n'
            ),
            "ops": [("replace", "expr.py", _e2_old, _e2_new)],
            "expect_targets": {"expr.py"},
        },
        {
            "instruction": (
                "请修改 expr.py 中的 evaluate(s)：应支持 - 运算符"
                "（与 + 同样从左到右），当前只处理 +。"
            ),
            "tests": (
                "import expr\n\n\n"
                "def test_sub():\n"
                '    assert expr.evaluate("5-2") == 3\n'
                '    assert expr.evaluate("8 - 3") == 5\n\n\n'
                "def test_add_regression():\n"
                '    assert expr.evaluate("1+2") == 3\n\n\n'
                "def test_mixed_left_to_right():\n"
                '    assert expr.evaluate("9-3+1") == 7\n'
            ),
            "ops": [("replace", "expr.py", _e3_old, _e3_new)],
            "expect_targets": {"expr.py"},
        },
        {
            "instruction": (
                "请修改 expr.py 中的 tokenize(s)："
                "应把连续数字合并为多位数 token"
                "（当前 \"12\" 被拆成 \"1\" 和 \"2\"）。"
            ),
            "tests": (
                "import expr\n\n\n"
                "def test_multi_digit_tokenize():\n"
                '    assert expr.tokenize("12+34") == ["12", "+", "34"]\n\n\n'
                "def test_multi_digit_eval():\n"
                '    assert expr.evaluate("12+34") == 46\n'
                '    assert expr.evaluate("100 - 40") == 60\n\n\n'
                "def test_single_digit_regression():\n"
                '    assert expr.evaluate("5-2") == 3\n'
            ),
            "ops": [("replace", "expr.py", _t4_old, _t4_new)],
            "expect_targets": {"expr.py"},
        },
        {
            "instruction": (
                "请修改 expr.py 中的 evaluate(s)：应支持 * 运算符"
                "（与 + - 同样从左到右），当前只处理 + 和 -。"
            ),
            "tests": (
                "import expr\n\n\n"
                "def test_mul():\n"
                '    assert expr.evaluate("3*4") == 12\n'
                '    assert expr.evaluate("6 * 7") == 42\n\n\n'
                "def test_chain():\n"
                '    assert expr.evaluate("2+3*4") == 20\n\n\n'
                "def test_multi_digit_regression():\n"
                '    assert expr.evaluate("12+34") == 46\n'
            ),
            "ops": [("replace", "expr.py", _e5_old, _e5_new)],
            "expect_targets": {"expr.py"},
        },
    ],
    info_points=[
        {"id": "ip_tokenize_ops", "type": "implementation",
         "value": "tokenizer 把 + - * / 分离为独立 token",
         "locator": "instruction:step1 + expr.py",
         "needed_by_steps": [1, 2, 4],
         "redundant_in_instruction": True},
        {"id": "ip_ltr_eval", "type": "implementation",
         "value": "evaluate 从左到右逐对处理运算符",
         "locator": "instruction:step2/3/5 + expr.py",
         "needed_by_steps": [2, 3, 5],
         "redundant_in_instruction": True},
        {"id": "ip_digit_group", "type": "implementation",
         "value": "连续数字合并为多位数 token",
         "locator": "instruction:step4 + expr.py",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": True},
        {"id": "ip_sub_history", "type": "history",
         "value": "evaluate(5-2)==3（step3 起保持）",
         "locator": "expr.py (step3) + step5 回归 eval",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：账单算式解析（不同结构：scan/run + acc 游标风格）
_bill_b = (
    '"""Bill expression runner."""\n\n\n'
    "def scan(s):\n"
    "    return s.split()\n\n\n"
    "def run(s):\n"
    "    for t in scan(s):\n"
    "        if t.isdigit():\n"
    "            return int(t)\n"
    "    return 0\n"
)
_r1_old = (
    "def scan(s):\n"
    "    return s.split()\n"
)
_r1_new = (
    "def scan(s):\n"
    "    out = []\n"
    "    for c in s:\n"
    '        if c in "+-*/":\n'
    "            out.append(c)\n"
    "        elif not c.isspace():\n"
    "            out.append(c)\n"
    "    return out\n"
)
_u2_old = (
    "def run(s):\n"
    "    for t in scan(s):\n"
    "        if t.isdigit():\n"
    "            return int(t)\n"
    "    return 0\n"
)
_u2_new = (
    "def run(s):\n"
    "    toks = scan(s)\n"
    "    acc = int(toks[0])\n"
    "    i = 1\n"
    "    while i < len(toks):\n"
    '        if toks[i] == "+":\n'
    "            acc = acc + int(toks[i + 1])\n"
    "        i += 2\n"
    "    return acc\n"
)
_u3_old = (
    '        if toks[i] == "+":\n'
    "            acc = acc + int(toks[i + 1])\n"
)
_u3_new = (
    '        if toks[i] == "+":\n'
    "            acc = acc + int(toks[i + 1])\n"
    '        elif toks[i] == "-":\n'
    "            acc = acc - int(toks[i + 1])\n"
)
_r4_old = (
    "def scan(s):\n"
    "    out = []\n"
    "    for c in s:\n"
    '        if c in "+-*/":\n'
    "            out.append(c)\n"
    "        elif not c.isspace():\n"
    "            out.append(c)\n"
    "    return out\n"
)
_r4_new = (
    "def scan(s):\n"
    "    out = []\n"
    '    buf = ""\n'
    "    for c in s:\n"
    '        if c in "+-*/":\n'
    "            if buf:\n"
    "                out.append(buf)\n"
    '                buf = ""\n'
    "            out.append(c)\n"
    "        elif c.isspace():\n"
    "            if buf:\n"
    "                out.append(buf)\n"
    '                buf = ""\n'
    "        else:\n"
    '            buf += c\n'
    "    if buf:\n"
    "        out.append(buf)\n"
    "    return out\n"
)
_u5_old = (
    '        if toks[i] == "+":\n'
    "            acc = acc + int(toks[i + 1])\n"
    '        elif toks[i] == "-":\n'
    "            acc = acc - int(toks[i + 1])\n"
)
_u5_new = (
    '        if toks[i] == "+":\n'
    "            acc = acc + int(toks[i + 1])\n"
    '        elif toks[i] == "-":\n'
    "            acc = acc - int(toks[i + 1])\n"
    '        elif toks[i] == "*":\n'
    "            acc = acc * int(toks[i + 1])\n"
)
T(
    id="ind_M06b",
    family="ind_med_parser",
    type="grammar_incremental",
    difficulty="medium",
    focus="账单算式解析增量：scan 分离运算符→加法→减法→多位数→乘法（scan/run 结构）",
    files={"billrun.py": _bill_b},
    steps=[
        {
            "instruction": (
                "请修改 billrun.py 中的 scan(s)："
                "应把 + - * / 从字符流中分离为独立元素"
                "（当前仅去除空白、运算符与数字粘连）。"
            ),
            "tests": (
                "import billrun\n\n\n"
                "def test_scan_ops():\n"
                '    assert billrun.scan("8+3") == ["8", "+", "3"]\n'
                '    assert billrun.scan("9-1") == ["9", "-", "1"]\n\n\n'
                "def test_scan_spaces():\n"
                '    assert billrun.scan("8 + 3") == ["8", "+", "3"]\n\n\n'
                "def test_run_regression():\n"
                '    assert billrun.run("7") == 7\n'
            ),
            "ops": [("replace", "billrun.py", _r1_old, _r1_new)],
            "expect_targets": {"billrun.py"},
        },
        {
            "instruction": (
                "请修改 billrun.py 中的 run(s)："
                "应按从左到右只处理 + 运算符求值"
                "（当前把所有数字字符直接累加）。"
            ),
            "tests": (
                "import billrun\n\n\n"
                "def test_add():\n"
                '    assert billrun.run("8+3") == 11\n'
                '    assert billrun.run("4 + 5") == 9\n\n\n'
                "def test_single():\n"
                '    assert billrun.run("7") == 7\n\n\n'
                "def test_scan_regression():\n"
                '    assert billrun.scan("8+3") == ["8", "+", "3"]\n'
            ),
            "ops": [("replace", "billrun.py", _u2_old, _u2_new)],
            "expect_targets": {"billrun.py"},
        },
        {
            "instruction": (
                "请修改 billrun.py 中的 run(s)：应支持 - 运算符"
                "（与 + 同样从左到右），当前只处理 +。"
            ),
            "tests": (
                "import billrun\n\n\n"
                "def test_sub():\n"
                '    assert billrun.run("8-3") == 5\n'
                '    assert billrun.run("7 - 2") == 5\n\n\n'
                "def test_add_regression():\n"
                '    assert billrun.run("8+3") == 11\n\n\n'
                "def test_mixed():\n"
                '    assert billrun.run("9-2+1") == 8\n'
            ),
            "ops": [("replace", "billrun.py", _u3_old, _u3_new)],
            "expect_targets": {"billrun.py"},
        },
        {
            "instruction": (
                "请修改 billrun.py 中的 scan(s)："
                "应把连续数字合并为多位数 token"
                "（当前 \"25\" 被拆成 \"2\" 和 \"5\"）。"
            ),
            "tests": (
                "import billrun\n\n\n"
                "def test_multi_scan():\n"
                '    assert billrun.scan("25+13") == ["25", "+", "13"]\n\n\n'
                "def test_multi_run():\n"
                '    assert billrun.run("25+13") == 38\n'
                '    assert billrun.run("100 - 40") == 60\n\n\n'
                "def test_single_regression():\n"
                '    assert billrun.run("8-3") == 5\n'
            ),
            "ops": [("replace", "billrun.py", _r4_old, _r4_new)],
            "expect_targets": {"billrun.py"},
        },
        {
            "instruction": (
                "请修改 billrun.py 中的 run(s)：应支持 * 运算符"
                "（与 + - 同样从左到右），当前只处理 + 和 -。"
            ),
            "tests": (
                "import billrun\n\n\n"
                "def test_mul():\n"
                '    assert billrun.run("6*7") == 42\n'
                '    assert billrun.run("5 * 8") == 40\n\n\n'
                "def test_chain():\n"
                '    assert billrun.run("2+3*4") == 20\n\n\n'
                "def test_multi_regression():\n"
                '    assert billrun.run("25+13") == 38\n'
            ),
            "ops": [("replace", "billrun.py", _u5_old, _u5_new)],
            "expect_targets": {"billrun.py"},
        },
    ],
    info_points=[
        {"id": "ip_scan_ops", "type": "implementation",
         "value": "scan 把 + - * / 分离为独立元素",
         "locator": "instruction:step1 + billrun.py",
         "needed_by_steps": [1, 2, 4],
         "redundant_in_instruction": True},
        {"id": "ip_run_ltr", "type": "implementation",
         "value": "run 从左到右逐对处理运算符（acc 游标风格）",
         "locator": "instruction:step2/3/5 + billrun.py",
         "needed_by_steps": [2, 3, 5],
         "redundant_in_instruction": True},
        {"id": "ip_bill_digits", "type": "implementation",
         "value": "连续数字合并为多位数 token",
         "locator": "instruction:step4 + billrun.py",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": True},
        {"id": "ip_run_history", "type": "history",
         "value": "run(8-3)==5（step3 起保持）",
         "locator": "billrun.py (step3) + step5 回归 eval",
         "needed_by_steps": [4, 5],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ MF7 ind_med_pipeline
# 变体 a：行清洗管道（config 默认 stages → 未知 stage 抛错 → trim → count → 改 config）
_cfg_pa = '{\n  "stages": ["load", "clean"]\n}\n'
_plg_a = (
    '"""Data pipeline."""\n\n'
    "import json\n"
    "from pathlib import Path\n\n\n"
    'def load_config(path="config.json"):\n'
    "    base = Path(__file__).resolve().parent\n"
    "    target = Path(path)\n"
    "    if not target.is_absolute():\n"
    "        target = base / target\n"
    '    return json.loads(target.read_text(encoding="utf-8"))\n\n\n'
    "def default_stages():\n"
    '    return ["load"]\n\n\n'
    "def run(rows, stages=None):\n"
    "    if stages is None:\n"
    "        stages = default_stages()\n"
    "    out = list(rows)\n"
    "    for name in stages:\n"
    '        if name == "load":\n'
    "            out = list(out)\n"
    '        elif name == "clean":\n'
    "            out = [r for r in out if r]\n"
    "    return out\n"
)
_p1_old = (
    "def default_stages():\n"
    '    return ["load"]\n'
)
_p1_new = (
    "def default_stages():\n"
    '    return load_config()["stages"]\n'
)
_p2_old = (
    "def run(rows, stages=None):\n"
    "    if stages is None:\n"
    "        stages = default_stages()\n"
    "    out = list(rows)\n"
    "    for name in stages:\n"
    '        if name == "load":\n'
    "            out = list(out)\n"
    '        elif name == "clean":\n'
    "            out = [r for r in out if r]\n"
    "    return out\n"
)
_p2_new = (
    "def run(rows, stages=None):\n"
    "    if stages is None:\n"
    "        stages = default_stages()\n"
    "    out = list(rows)\n"
    "    for name in stages:\n"
    '        if name == "load":\n'
    "            out = list(out)\n"
    '        elif name == "clean":\n'
    "            out = [r for r in out if r]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
    "    return out\n"
)
_p3_old = (
    '        elif name == "clean":\n'
    "            out = [r for r in out if r]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
)
_p3_new = (
    '        elif name == "clean":\n'
    "            out = [r for r in out if r]\n"
    '        elif name == "trim":\n'
    "            out = [r.strip() if isinstance(r, str) else r for r in out]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
)
_p4_old = (
    '        elif name == "trim":\n'
    "            out = [r.strip() if isinstance(r, str) else r for r in out]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
)
_p4_new = (
    '        elif name == "trim":\n'
    "            out = [r.strip() if isinstance(r, str) else r for r in out]\n"
    '        elif name == "count":\n'
    "            out = [len(out)]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
)
_cfg_pa_v2 = '{\n  "stages": ["load", "trim", "clean"]\n}\n'
T(
    id="ind_M07a",
    family="ind_med_pipeline",
    type="config_driven_pipeline",
    difficulty="medium",
    focus="行清洗管道：config 默认 stages→未知 stage 抛错→trim→count→改 config 默认",
    files={"config.json": _cfg_pa, "pipeline.py": _plg_a},
    steps=[
        {
            "instruction": (
                "请修改 pipeline.py 中的 default_stages()："
                "应返回从配置读入的 stages 列表。"
                "stages 键在 config.json 中。"
            ),
            "tests": (
                "import pipeline\n\n\n"
                "def test_reads_config():\n"
                "    assert pipeline.default_stages() == [\"load\", \"clean\"]\n\n\n"
                "def test_run_uses_default():\n"
                "    assert pipeline.run([\"a\", \"\", \"b\"]) == [\"a\", \"b\"]\n"
            ),
            "ops": [("replace", "pipeline.py", _p1_old, _p1_new)],
            "expect_targets": {"pipeline.py"},
        },
        {
            "instruction": (
                "请修改 pipeline.py 中的 run(rows, stages)："
                "遇到未知 stage 名应抛出 ValueError"
                "（当前静默忽略未知名）。"
            ),
            "tests": (
                "import pytest\n"
                "import pipeline\n\n\n"
                "def test_unknown_stage():\n"
                "    with pytest.raises(ValueError):\n"
                '        pipeline.run(["a"], ["nope"])\n\n\n'
                "def test_known_still_works():\n"
                '    assert pipeline.run(["a", ""], ["load", "clean"]) == ["a"]\n\n\n'
                "def test_default_regression():\n"
                "    assert pipeline.default_stages() == [\"load\", \"clean\"]\n"
            ),
            "ops": [("replace", "pipeline.py", _p2_old, _p2_new)],
            "expect_targets": {"pipeline.py"},
        },
        {
            "instruction": (
                "pipeline.py 的 run(rows, stages) 应新增 trim 阶段："
                "对字符串元素去除首尾空白，非字符串原样保留；"
                "当前管线尚无该阶段。"
            ),
            "tests": (
                "import pipeline\n\n\n"
                "def test_trim_stage():\n"
                '    assert pipeline.run(["  a  ", 3], ["trim"]) == ["a", 3]\n\n\n'
                "def test_unknown_regression():\n"
                "    import pytest\n"
                "    with pytest.raises(ValueError):\n"
                '        pipeline.run(["a"], ["nope"])\n\n\n'
                "def test_clean_regression():\n"
                '    assert pipeline.run(["a", " "], ["trim", "clean"]) == ["a"]\n'
            ),
            "ops": [("replace", "pipeline.py", _p3_old, _p3_new)],
            "expect_targets": {"pipeline.py"},
        },
        {
            "instruction": (
                "pipeline.py 的 run(rows, stages) 应新增 count 阶段："
                "把当前行列表替换为单元素列表 [长度]；"
                "当前管线尚无该阶段。"
            ),
            "tests": (
                "import pipeline\n\n\n"
                "def test_count_stage():\n"
                '    assert pipeline.run(["a", "b", "c"], ["count"]) == [3]\n\n\n'
                "def test_count_after_clean():\n"
                '    assert pipeline.run(["a", ""], ["clean", "count"]) == [1]\n\n\n'
                "def test_trim_regression():\n"
                '    assert pipeline.run(["  x "], ["trim"]) == ["x"]\n'
            ),
            "ops": [("replace", "pipeline.py", _p4_old, _p4_new)],
            "expect_targets": {"pipeline.py"},
        },
        {
            "instruction": (
                "config.json 中 stages 应为 "
                "[\"load\", \"trim\", \"clean\"]"
                "（当前为 [\"load\", \"clean\"]）。"
            ),
            "tests": (
                "import pipeline\n\n\n"
                "def test_new_default():\n"
                "    assert pipeline.default_stages() == [\n"
                '        "load", "trim", "clean"]\n\n\n'
                "def test_run_with_new_default():\n"
                '    out = pipeline.run(["  a  ", "", " b "])\n'
                '    assert out == ["a", "b"]\n\n\n'
                "def test_count_regression():\n"
                '    assert pipeline.run(["a", "b"], ["count"]) == [2]\n'
            ),
            "ops": [
                ("replace", "config.json",
                 '"stages": ["load", "clean"]',
                 '"stages": ["load", "trim", "clean"]'),
            ],
            "expect_targets": {"config.json"},
        },
    ],
    info_points=[
        {"id": "ip_config_stages", "type": "critical_data",
         "value": "config.json stages 键驱动 default_stages",
         "locator": "config.json（指令不复述键路径细节）",
         "needed_by_steps": [1, 5],
         "redundant_in_instruction": False},
        {"id": "ip_unknown_raises", "type": "implementation",
         "value": "未知 stage → ValueError",
         "locator": "instruction:step2 + pipeline.py",
         "needed_by_steps": [2, 3, 4],
         "redundant_in_instruction": True},
        {"id": "ip_trim_semantics", "type": "implementation",
         "value": "trim：字符串 strip，非字符串保留",
         "locator": "instruction:step3 + pipeline.py",
         "needed_by_steps": [3, 5],
         "redundant_in_instruction": True},
        {"id": "ip_count_semantics", "type": "implementation",
         "value": "count：out = [len(out)]",
         "locator": "instruction:step4 + pipeline.py",
         "needed_by_steps": [4],
         "redundant_in_instruction": True},
    ],
)

# 变体 b：指标聚合管道（settings 默认 flow → 未知 flow 抛错 → upper → total → 改 settings）
_set_pb = '{\n  "flow": ["read", "dedupe"]\n}\n'
_flow_b = (
    '"""Metric flow."""\n\n'
    "import json\n"
    "from pathlib import Path\n\n\n"
    'def read_settings(path="settings.json"):\n'
    "    base = Path(__file__).resolve().parent\n"
    "    target = Path(path)\n"
    "    if not target.is_absolute():\n"
    "        target = base / target\n"
    "    return json.loads(target.read_text(encoding=\"utf-8\"))\n\n\n"
    "def default_flow():\n"
    '    return ["read"]\n\n\n'
    "def execute(rows, flow=None):\n"
    "    if flow is None:\n"
    "        flow = default_flow()\n"
    "    out = list(rows)\n"
    "    for name in flow:\n"
    '        if name == "read":\n'
    "            out = list(out)\n"
    '        elif name == "dedupe":\n'
    "            seen = set()\n"
    "            out = [r for r in out if not (r in seen or seen.add(r))]\n"
    "    return out\n"
)
_f1_old = (
    "def default_flow():\n"
    '    return ["read"]\n'
)
_f1_new = (
    "def default_flow():\n"
    '    return read_settings()["flow"]\n'
)
_f2_old = (
    "def execute(rows, flow=None):\n"
    "    if flow is None:\n"
    "        flow = default_flow()\n"
    "    out = list(rows)\n"
    "    for name in flow:\n"
    '        if name == "read":\n'
    "            out = list(out)\n"
    '        elif name == "dedupe":\n'
    "            seen = set()\n"
    "            out = [r for r in out if not (r in seen or seen.add(r))]\n"
    "    return out\n"
)
_f2_new = (
    "def execute(rows, flow=None):\n"
    "    if flow is None:\n"
    "        flow = default_flow()\n"
    "    out = list(rows)\n"
    "    for name in flow:\n"
    '        if name == "read":\n'
    "            out = list(out)\n"
    '        elif name == "dedupe":\n'
    "            seen = set()\n"
    "            out = [r for r in out if not (r in seen or seen.add(r))]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
    "    return out\n"
)
_f3_old = (
    '        elif name == "dedupe":\n'
    "            seen = set()\n"
    "            out = [r for r in out if not (r in seen or seen.add(r))]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
)
_f3_new = (
    '        elif name == "dedupe":\n'
    "            seen = set()\n"
    "            out = [r for r in out if not (r in seen or seen.add(r))]\n"
    '        elif name == "upper":\n'
    "            out = [r.upper() if isinstance(r, str) else r for r in out]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
)
_f4_old = (
    '        elif name == "upper":\n'
    "            out = [r.upper() if isinstance(r, str) else r for r in out]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
)
_f4_new = (
    '        elif name == "upper":\n'
    "            out = [r.upper() if isinstance(r, str) else r for r in out]\n"
    '        elif name == "total":\n'
    "            out = [sum(x for x in out if isinstance(x, (int, float)))]\n"
    "        else:\n"
    '            raise ValueError(name)\n'
)
_set_pb_v2 = '{\n  "flow": ["read", "upper", "dedupe"]\n}\n'
T(
    id="ind_M07b",
    family="ind_med_pipeline",
    type="config_driven_pipeline",
    difficulty="medium",
    focus="指标聚合管道：settings 默认 flow→未知 flow 抛错→upper→total→改 settings 默认",
    files={"settings.json": _set_pb, "flow.py": _flow_b},
    steps=[
        {
            "instruction": (
                "请修改 flow.py 中的 default_flow()："
                "应返回从配置读入的 flow 列表。"
                "flow 键在 settings.json 中。"
            ),
            "tests": (
                "import flow\n\n\n"
                "def test_reads_settings():\n"
                '    assert flow.default_flow() == ["read", "dedupe"]\n\n\n'
                "def test_execute_uses_default():\n"
                '    assert flow.execute(["a", "a", "b"]) == ["a", "b"]\n'
            ),
            "ops": [("replace", "flow.py", _f1_old, _f1_new)],
            "expect_targets": {"flow.py"},
        },
        {
            "instruction": (
                "请修改 flow.py 中的 execute(rows, flow)："
                "遇到未知 flow 名应抛出 ValueError"
                "（当前静默忽略未知名）。"
            ),
            "tests": (
                "import pytest\n"
                "import flow\n\n\n"
                "def test_unknown_flow():\n"
                "    with pytest.raises(ValueError):\n"
                '        flow.execute(["a"], ["nope"])\n\n\n'
                "def test_known_still_works():\n"
                '    assert flow.execute(["x", "x"], ["dedupe"]) == ["x"]\n\n\n'
                "def test_default_regression():\n"
                '    assert flow.default_flow() == ["read", "dedupe"]\n'
            ),
            "ops": [("replace", "flow.py", _f2_old, _f2_new)],
            "expect_targets": {"flow.py"},
        },
        {
            "instruction": (
                "flow.py 的 execute(rows, flow) 应新增 upper 阶段："
                "对字符串元素转大写，非字符串原样保留；"
                "当前流程尚无该阶段。"
            ),
            "tests": (
                "import flow\n\n\n"
                "def test_upper_stage():\n"
                '    assert flow.execute(["ab", 5], ["upper"]) == ["AB", 5]\n\n\n'
                "def test_unknown_regression():\n"
                "    import pytest\n"
                "    with pytest.raises(ValueError):\n"
                '        flow.execute(["a"], ["nope"])\n\n\n'
                "def test_dedupe_regression():\n"
                '    assert flow.execute(["a", "a"], ["dedupe"]) == ["a"]\n'
            ),
            "ops": [("replace", "flow.py", _f3_old, _f3_new)],
            "expect_targets": {"flow.py"},
        },
        {
            "instruction": (
                "flow.py 的 execute(rows, flow) 应新增 total 阶段："
                "把当前列表替换为单元素列表 [数值元素之和]；"
                "当前流程尚无该阶段。"
            ),
            "tests": (
                "import flow\n\n\n"
                "def test_total_stage():\n"
                '    assert flow.execute([1, 2, 3], ["total"]) == [6]\n\n\n'
                "def test_total_ignores_non_numeric():\n"
                '    assert flow.execute([1, "x", 2], ["total"]) == [3]\n\n\n'
                "def test_upper_regression():\n"
                '    assert flow.execute(["ab"], ["upper"]) == ["AB"]\n'
            ),
            "ops": [("replace", "flow.py", _f4_old, _f4_new)],
            "expect_targets": {"flow.py"},
        },
        {
            "instruction": (
                "settings.json 中 flow 应为 "
                "[\"read\", \"upper\", \"dedupe\"]"
                "（当前为 [\"read\", \"dedupe\"]）。"
            ),
            "tests": (
                "import flow\n\n\n"
                "def test_new_default():\n"
                '    assert flow.default_flow() == ["read", "upper", "dedupe"]\n\n\n'
                "def test_execute_with_new_default():\n"
                '    out = flow.execute(["ab", "ab", "cd"])\n'
                '    assert out == ["AB", "CD"]\n\n\n'
                "def test_total_regression():\n"
                '    assert flow.execute([2, 3], ["total"]) == [5]\n'
            ),
            "ops": [
                ("replace", "settings.json",
                 '"flow": ["read", "dedupe"]',
                 '"flow": ["read", "upper", "dedupe"]'),
            ],
            "expect_targets": {"settings.json"},
        },
    ],
    info_points=[
        {"id": "ip_flow_settings", "type": "critical_data",
         "value": "settings.json flow 键驱动 default_flow",
         "locator": "settings.json（指令不复述键路径细节）",
         "needed_by_steps": [1, 5],
         "redundant_in_instruction": False},
        {"id": "ip_unknown_flow", "type": "implementation",
         "value": "未知 flow 名 → ValueError",
         "locator": "instruction:step2 + flow.py",
         "needed_by_steps": [2, 3, 4],
         "redundant_in_instruction": True},
        {"id": "ip_upper_semantics", "type": "implementation",
         "value": "upper：字符串 upper，非字符串保留",
         "locator": "instruction:step3 + flow.py",
         "needed_by_steps": [3, 5],
         "redundant_in_instruction": True},
        {"id": "ip_total_semantics", "type": "implementation",
         "value": "total：[sum(数值元素)]",
         "locator": "instruction:step4 + flow.py",
         "needed_by_steps": [4],
         "redundant_in_instruction": True},
    ],
)

# ============================================================ MF8 ind_med_registry
# 变体 a：命令注册表（UnknownCommand → alias → None→"ok" → app 注册 → names 注册序）
_reg_a = (
    '"""Command registry."""\n\n\n'
    "COMMANDS = {}\n\n\n"
    "def register(name, fn):\n"
    "    COMMANDS[name] = fn\n\n\n"
    "def dispatch(name, arg):\n"
    "    if name not in COMMANDS:\n"
    '        raise KeyError(name)\n'
    "    return COMMANDS[name](arg)\n\n\n"
    "def names():\n"
    "    return sorted(COMMANDS)\n"
)
_app_a = (
    '"""Tiny app."""\n\n'
    "from registry import register, dispatch\n\n\n"
    "def hello(arg):\n"
    '    return f"hi {arg}"\n\n\n'
    'register("hello", hello)\n'
)
_r1_old = (
    "def dispatch(name, arg):\n"
    "    if name not in COMMANDS:\n"
    '        raise KeyError(name)\n'
    "    return COMMANDS[name](arg)\n"
)
_r1_new = (
    "class UnknownCommand(Exception):\n"
    "    pass\n\n\n"
    "def dispatch(name, arg):\n"
    "    if name not in COMMANDS:\n"
    "        raise UnknownCommand(name)\n"
    "    return COMMANDS[name](arg)\n"
)
_r2_old = (
    "def dispatch(name, arg):\n"
    "    if name not in COMMANDS:\n"
    "        raise UnknownCommand(name)\n"
    "    return COMMANDS[name](arg)\n"
)
_r2_new = (
    "ALIASES = {}\n\n\n"
    "def register_alias(alias, target):\n"
    "    ALIASES[alias] = target\n\n\n"
    "def dispatch(name, arg):\n"
    "    name = ALIASES.get(name, name)\n"
    "    if name not in COMMANDS:\n"
    "        raise UnknownCommand(name)\n"
    "    return COMMANDS[name](arg)\n"
)
_r3_old = (
    "def dispatch(name, arg):\n"
    "    name = ALIASES.get(name, name)\n"
    "    if name not in COMMANDS:\n"
    "        raise UnknownCommand(name)\n"
    "    return COMMANDS[name](arg)\n"
)
_r3_new = (
    "def dispatch(name, arg):\n"
    "    name = ALIASES.get(name, name)\n"
    "    if name not in COMMANDS:\n"
    "        raise UnknownCommand(name)\n"
    "    out = COMMANDS[name](arg)\n"
    "    if out is None:\n"
    '        return "ok"\n'
    "    return out\n"
)
_app_a2_old = (
    "def hello(arg):\n"
    '    return f"hi {arg}"\n\n\n'
    'register("hello", hello)\n'
)
_app_a2_new = (
    "def hello(arg):\n"
    '    return f"hi {arg}"\n\n\n'
    "def bye(arg):\n"
    '    return f"bye {arg}"\n\n\n'
    'register("hello", hello)\n'
    'register("bye", bye)\n'
)
_r5_old = (
    "def register(name, fn):\n"
    "    COMMANDS[name] = fn\n"
)
_r5_new = (
    "ORDER = []\n\n\n"
    "def register(name, fn):\n"
    "    if name not in COMMANDS:\n"
    "        ORDER.append(name)\n"
    "    COMMANDS[name] = fn\n"
)
_r5n_old = (
    "def names():\n"
    "    return sorted(COMMANDS)\n"
)
_r5n_new = (
    "def names():\n"
    "    return list(ORDER)\n"
)
T(
    id="ind_M08a",
    family="ind_med_registry",
    type="registry_dispatch_growth",
    difficulty="medium",
    focus="命令注册表：UnknownCommand→alias→None 返回 ok→app 注册 bye→names 注册序",
    files={"registry.py": _reg_a, "app.py": _app_a},
    steps=[
        {
            "instruction": (
                "请修改 registry.py 中的 dispatch(name, arg)："
                "未注册命令应抛出自定义异常 UnknownCommand"
                "（异常类定义在 registry.py，当前抛 KeyError）。"
            ),
            "tests": (
                "import pytest\n"
                "import registry\n\n\n"
                "def test_unknown():\n"
                "    with pytest.raises(registry.UnknownCommand):\n"
                '        registry.dispatch("zz", "")\n\n\n'
                "def test_known():\n"
                '    registry.register("t", lambda a: a)\n'
                '    assert registry.dispatch("t", "x") == "x"\n\n\n'
                "def test_names_regression():\n"
                '    assert "t" in registry.names()\n'
            ),
            "ops": [("replace", "registry.py", _r1_old, _r1_new)],
            "expect_targets": {"registry.py"},
        },
        {
            "instruction": (
                "registry.py 新增 register_alias(alias, target)："
                "把别名映射到已注册命令，dispatch 时先经别名解析再查表。"
            ),
            "tests": (
                "import registry\n\n\n"
                "def test_alias():\n"
                '    registry.register("greet", lambda a: "hola " + a)\n'
                '    registry.register_alias("hi2", "greet")\n'
                '    assert registry.dispatch("hi2", "bob") == "hola bob"\n\n\n'
                "def test_unknown_regression():\n"
                "    import pytest\n"
                "    with pytest.raises(registry.UnknownCommand):\n"
                '        registry.dispatch("nope", "")\n'
            ),
            "ops": [("replace", "registry.py", _r2_old, _r2_new)],
            "expect_targets": {"registry.py"},
        },
        {
            "instruction": (
                "请修改 registry.py 中的 dispatch(name, arg)："
                "命令返回 None 时应改为返回字符串 \"ok\""
                "（其他返回值原样透传）。"
            ),
            "tests": (
                "import registry\n\n\n"
                "def test_none_becomes_ok():\n"
                "    registry.register(\"silent\", lambda a: None)\n"
                '    assert registry.dispatch("silent", 1) == "ok"\n\n\n'
                "def test_passthrough():\n"
                '    registry.register("loud", lambda a: a * 2)\n'
                '    assert registry.dispatch("loud", 3) == 6\n\n\n'
                "def test_alias_regression():\n"
                '    registry.register("g2", lambda a: "g")\n'
                '    registry.register_alias("a2", "g2")\n'
                '    assert registry.dispatch("a2", None) == "g"\n'
            ),
            "ops": [("replace", "registry.py", _r3_old, _r3_new)],
            "expect_targets": {"registry.py"},
        },
        {
            "instruction": (
                "app.py 新增 bye 命令：函数 bye(arg) 返回 "
                "\"bye {arg}\" 形式，并完成名为 \"bye\" 的命令注册。"
            ),
            "tests": (
                "import app\n"
                "import registry\n\n\n"
                "def test_bye_registered():\n"
                '    assert registry.dispatch("bye", "now") == "bye now"\n\n\n'
                "def test_hello_regression():\n"
                '    assert registry.dispatch("hello", "there") == "hi there"\n\n\n'
                "def test_none_ok_regression():\n"
                '    registry.register("s2", lambda a: None)\n'
                '    assert registry.dispatch("s2", 0) == "ok"\n'
            ),
            "ops": [("replace", "app.py", _app_a2_old, _app_a2_new)],
            "expect_targets": {"app.py"},
        },
        {
            "instruction": (
                "请修改 registry.py 中的 names()："
                "应按注册顺序返回命令名列表"
                "（当前按字典序排序返回）。"
            ),
            "tests": (
                "import registry\n\n\n"
                "def test_registration_order():\n"
                "    registry.COMMANDS.clear()\n"
                "    registry.ORDER.clear()\n"
                '    registry.register("zebra", lambda a: 1)\n'
                '    registry.register("alpha", lambda a: 2)\n'
                '    assert registry.names() == ["zebra", "alpha"]\n\n\n'
                "def test_dispatch_still_works():\n"
                '    assert registry.dispatch("zebra", "") == 1\n\n\n'
                "def test_unknown_regression():\n"
                "    import pytest\n"
                "    with pytest.raises(registry.UnknownCommand):\n"
                '        registry.dispatch("ghost", "")\n'
            ),
            "ops": [
                ("replace", "registry.py", _r5_old, _r5_new),
                ("replace", "registry.py", _r5n_old, _r5n_new),
            ],
            "expect_targets": {"registry.py"},
        },
    ],
    info_points=[
        {"id": "ip_unknown_exc", "type": "interface",
         "value": "UnknownCommand（registry.py 定义）取代 KeyError",
         "locator": "instruction:step1 + registry.py",
         "needed_by_steps": [1, 2, 5],
         "redundant_in_instruction": True},
        {"id": "ip_alias_resolution", "type": "implementation",
         "value": "dispatch 先 ALIASES.get(name, name) 再查表",
         "locator": "instruction:step2 + registry.py",
         "needed_by_steps": [2, 3],
         "redundant_in_instruction": True},
        {"id": "ip_none_ok", "type": "implementation",
         "value": "命令返回 None → dispatch 返回 \"ok\"",
         "locator": "instruction:step3 + registry.py",
         "needed_by_steps": [3, 4],
         "redundant_in_instruction": True},
        {"id": "ip_order_history", "type": "history",
         "value": "ORDER 记录注册序（step5 前 names 为 sorted）",
         "locator": "registry.py (step5) + step5 eval",
         "needed_by_steps": [5],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：路由注册表（UnknownRoute → alias 路径 → None→"ok" → app 注册 → names 注册序）
_rou_b = (
    '"""Route registry."""\n\n\n'
    "ROUTES = {}\n\n\n"
    "def bind(path, handler):\n"
    "    ROUTES[path] = handler\n\n\n"
    "def serve(path, payload):\n"
    "    if path not in ROUTES:\n"
    '        raise KeyError(path)\n'
    "    return ROUTES[path](payload)\n\n\n"
    "def paths():\n"
    "    return sorted(ROUTES)\n"
)
_web_b = (
    '"""Web glue."""\n\n'
    "from routes import bind, serve\n\n\n"
    "def index(payload):\n"
    '    return f"index:{payload}"\n\n\n'
    'bind("/", index)\n'
)
_v1_old = (
    "def serve(path, payload):\n"
    "    if path not in ROUTES:\n"
    '        raise KeyError(path)\n'
    "    return ROUTES[path](payload)\n"
)
_v1_new = (
    "class UnknownRoute(Exception):\n"
    "    pass\n\n\n"
    "def serve(path, payload):\n"
    "    if path not in ROUTES:\n"
    "        raise UnknownRoute(path)\n"
    "    return ROUTES[path](payload)\n"
)
_v2_old = (
    "def serve(path, payload):\n"
    "    if path not in ROUTES:\n"
    "        raise UnknownRoute(path)\n"
    "    return ROUTES[path](payload)\n"
)
_v2_new = (
    "ALIASES = {}\n\n\n"
    "def bind_alias(alias, path):\n"
    "    ALIASES[alias] = path\n\n\n"
    "def serve(path, payload):\n"
    "    path = ALIASES.get(path, path)\n"
    "    if path not in ROUTES:\n"
    "        raise UnknownRoute(path)\n"
    "    return ROUTES[path](payload)\n"
)
_v3_old = (
    "def serve(path, payload):\n"
    "    path = ALIASES.get(path, path)\n"
    "    if path not in ROUTES:\n"
    "        raise UnknownRoute(path)\n"
    "    return ROUTES[path](payload)\n"
)
_v3_new = (
    "def serve(path, payload):\n"
    "    path = ALIASES.get(path, path)\n"
    "    if path not in ROUTES:\n"
    "        raise UnknownRoute(path)\n"
    "    out = ROUTES[path](payload)\n"
    "    if out is None:\n"
    '        return "ok"\n'
    "    return out\n"
)
_web_b2_old = (
    "def index(payload):\n"
    '    return f"index:{payload}"\n\n\n'
    'bind("/", index)\n'
)
_web_b2_new = (
    "def index(payload):\n"
    '    return f"index:{payload}"\n\n\n'
    "def health(payload):\n"
    '    return "up"\n\n\n'
    'bind("/", index)\n'
    'bind("/health", health)\n'
)
_v5_old = (
    "def bind(path, handler):\n"
    "    ROUTES[path] = handler\n"
)
_v5_new = (
    "ORDER = []\n\n\n"
    "def bind(path, handler):\n"
    "    if path not in ROUTES:\n"
    "        ORDER.append(path)\n"
    "    ROUTES[path] = handler\n"
)
_v5p_old = (
    "def paths():\n"
    "    return sorted(ROUTES)\n"
)
_v5p_new = (
    "def paths():\n"
    "    return list(ORDER)\n"
)
T(
    id="ind_M08b",
    family="ind_med_registry",
    type="registry_dispatch_growth",
    difficulty="medium",
    focus="路由注册表：UnknownRoute→alias→None 返回 ok→app 注册 /health→paths 注册序",
    files={"routes.py": _rou_b, "web.py": _web_b},
    steps=[
        {
            "instruction": (
                "请修改 routes.py 中的 serve(path, payload)："
                "未注册路径应抛出自定义异常 UnknownRoute"
                "（异常类定义在 routes.py，当前抛 KeyError）。"
            ),
            "tests": (
                "import pytest\n"
                "import routes\n\n\n"
                "def test_unknown_route():\n"
                "    with pytest.raises(routes.UnknownRoute):\n"
                '        routes.serve("/zz", "")\n\n\n'
                "def test_known_route():\n"
                '    routes.bind("/x", lambda p: p)\n'
                '    assert routes.serve("/x", 9) == 9\n\n\n'
                "def test_paths_regression():\n"
                '    assert "/x" in routes.paths()\n'
            ),
            "ops": [("replace", "routes.py", _v1_old, _v1_new)],
            "expect_targets": {"routes.py"},
        },
        {
            "instruction": (
                "routes.py 新增 bind_alias(alias, path)："
                "把别名映射到已注册路径，serve 时先经别名解析再查表。"
            ),
            "tests": (
                "import routes\n\n\n"
                "def test_bind_alias():\n"
                '    routes.bind("/home", lambda p: "H")\n'
                '    routes.bind_alias("/h", "/home")\n'
                '    assert routes.serve("/h", None) == "H"\n\n\n'
                "def test_unknown_regression():\n"
                "    import pytest\n"
                "    with pytest.raises(routes.UnknownRoute):\n"
                '        routes.serve("/ghost", "")\n'
            ),
            "ops": [("replace", "routes.py", _v2_old, _v2_new)],
            "expect_targets": {"routes.py"},
        },
        {
            "instruction": (
                "请修改 routes.py 中的 serve(path, payload)："
                "处理器返回 None 时应改为返回字符串 \"ok\""
                "（其他返回值原样透传）。"
            ),
            "tests": (
                "import routes\n\n\n"
                "def test_none_becomes_ok():\n"
                '    routes.bind("/void", lambda p: None)\n'
                '    assert routes.serve("/void", 1) == "ok"\n\n\n'
                "def test_passthrough():\n"
                '    routes.bind("/dbl", lambda p: p + p)\n'
                '    assert routes.serve("/dbl", 4) == 8\n\n\n'
                "def test_alias_regression():\n"
                '    routes.bind("/hm", lambda p: "y")\n'
                '    routes.bind_alias("/h2", "/hm")\n'
                '    assert routes.serve("/h2", None) == "y"\n'
            ),
            "ops": [("replace", "routes.py", _v3_old, _v3_new)],
            "expect_targets": {"routes.py"},
        },
        {
            "instruction": (
                "web.py 新增 health 处理器：health(payload) 返回 \"up\"，"
                "并完成路径 \"/health\" 的绑定注册。"
            ),
            "tests": (
                "import web\n"
                "import routes\n\n\n"
                "def test_health_bound():\n"
                '    assert routes.serve("/health", None) == "up"\n\n\n'
                "def test_index_regression():\n"
                '    assert routes.serve("/", "q") == "index:q"\n\n\n'
                "def test_none_ok_regression():\n"
                '    routes.bind("/void2", lambda p: None)\n'
                '    assert routes.serve("/void2", 0) == "ok"\n'
            ),
            "ops": [("replace", "web.py", _web_b2_old, _web_b2_new)],
            "expect_targets": {"web.py"},
        },
        {
            "instruction": (
                "请修改 routes.py 中的 paths()："
                "应按注册顺序返回路径列表"
                "（当前按字典序排序返回）。"
            ),
            "tests": (
                "import routes\n\n\n"
                "def test_registration_order():\n"
                "    routes.ROUTES.clear()\n"
                "    routes.ORDER.clear()\n"
                '    routes.bind("/zeta", lambda p: 1)\n'
                '    routes.bind("/alpha", lambda p: 2)\n'
                '    assert routes.paths() == ["/zeta", "/alpha"]\n\n\n'
                "def test_serve_still_works():\n"
                '    assert routes.serve("/zeta", "") == 1\n\n\n'
                "def test_unknown_regression():\n"
                "    import pytest\n"
                "    with pytest.raises(routes.UnknownRoute):\n"
                '        routes.serve("/ghost", "")\n'
            ),
            "ops": [
                ("replace", "routes.py", _v5_old, _v5_new),
                ("replace", "routes.py", _v5p_old, _v5p_new),
            ],
            "expect_targets": {"routes.py"},
        },
    ],
    info_points=[
        {"id": "ip_unknown_route", "type": "interface",
         "value": "UnknownRoute（routes.py 定义）取代 KeyError",
         "locator": "instruction:step1 + routes.py",
         "needed_by_steps": [1, 2, 5],
         "redundant_in_instruction": True},
        {"id": "ip_alias_paths", "type": "implementation",
         "value": "serve 先 ALIASES.get(path, path) 再查表",
         "locator": "instruction:step2 + routes.py",
         "needed_by_steps": [2, 3],
         "redundant_in_instruction": True},
        {"id": "ip_none_ok_route", "type": "implementation",
         "value": "处理器返回 None → serve 返回 \"ok\"",
         "locator": "instruction:step3 + routes.py",
         "needed_by_steps": [3, 4],
         "redundant_in_instruction": True},
        {"id": "ip_paths_history", "type": "history",
         "value": "ORDER 记录绑定序（step5 前 paths 为 sorted）",
         "locator": "routes.py (step5) + step5 eval",
         "needed_by_steps": [5],
         "redundant_in_instruction": False},
    ],
)
