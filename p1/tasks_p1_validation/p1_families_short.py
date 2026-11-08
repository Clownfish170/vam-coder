"""P1 Short 族（4 族 × 4 变体 = 16 题，每题 2 步）。由 make_p1_tasks 导入注册。"""

from p1_registry import T

# ============================================================ SF1 规格修改
_SF1 = [
    dict(n="01", doc="Threshold gate utilities", f_rule="adjust", f_base="keep",
         f_new="adjust_pair", wrong="v * 2", mult=5, aux="bump", inc=1, tag="gate"),
    dict(n="02", doc="Weight scaling helpers", f_rule="scale_w", f_base="raw_w",
         f_new="scale_pair", wrong="v * 3", mult=6, aux="nudge", inc=2, tag="weight"),
    dict(n="03", doc="Score normalization core", f_rule="norm_score", f_base="clip_score",
         f_new="norm_pair", wrong="v + 2", mult=4, aux="shift", inc=3, tag="score"),
    dict(n="04", doc="Tier computation module", f_rule="tier_of", f_base="plain",
         f_new="tier_pair", wrong="v - 1", mult=7, aux="bump_tier", inc=4, tag="tier"),
]

for p in _SF1:
    core = (
        f'"""{p["doc"]}"""\n\n\n'
        f'def {p["f_rule"]}(v):\n'
        f'    return {p["wrong"]}\n\n\n'
        f'def {p["f_base"]}(v):\n'
        f'    return v\n'
    )
    aux = (
        '"""Side helpers."""\n\n\n'
        f'def {p["aux"]}(k):\n'
        f'    return k + {p["inc"]}\n'
    )
    notes = (
        '"""Unrelated notes."""\n\n\n'
        f'def tag():\n'
        f'    return "{p["tag"]}-notes"\n'
    )
    rule_old = f'def {p["f_rule"]}(v):\n    return {p["wrong"]}\n'
    rule_new = (
        f'def {p["f_rule"]}(v):\n'
        f'    if v < 0:\n'
        f'        return 0\n'
        f'    return v * {p["mult"]}\n'
    )
    new_fn_old = f'def {p["f_base"]}(v):\n    return v\n'
    new_fn_new = (
        f'def {p["f_base"]}(v):\n'
        f'    return v\n\n\n'
        f'def {p["f_new"]}(n):\n'
        f'    return {p["f_rule"]}(n) + {p["f_base"]}(n)\n'
    )
    m = p["mult"]
    tests1 = (
        "import core\n\n\n"
        "def test_negative_zero():\n"
        f"    assert core.{p['f_rule']}(-2) == 0\n"
        f"    assert core.{p['f_rule']}(0) == 0\n\n\n"
        "def test_positive_mult():\n"
        f"    assert core.{p['f_rule']}(3) == {3 * m}\n"
        f"    assert core.{p['f_rule']}(5) == {5 * m}\n\n\n"
        "def test_base_unchanged():\n"
        f"    assert core.{p['f_base']}(7) == 7\n"
    )
    tests2 = (
        "import core\n\n\n"
        "def test_new_fn():\n"
        f"    assert core.{p['f_new']}(2) == {2 * m} + 2\n"
        f"    assert core.{p['f_new']}(-1) == -1\n\n\n"
        "def test_rule_regression():\n"
        f"    assert core.{p['f_rule']}(-2) == 0\n"
        f"    assert core.{p['f_rule']}(3) == {3 * m}\n\n\n"
        "def test_aux_regression():\n"
        f"    assert core.__name__ == 'core'\n"
    )
    T(
        id=f"p1_S{p['n']}a",
        family="p1_short_spec",
        type="single_file_spec",
        difficulty="short",
        focus="单文件规格修改 + 第二步嵌入回归",
        files={"core.py": core, "aux.py": aux, "notes.py": notes},
        steps=[
            {
                "instruction": (
                    f"请修改 core.py 中的 {p['f_rule']}(v)：v < 0 应返回 0，"
                    f"v ≥ 0 应返回 v * {m}（当前实现为 {p['wrong']}）。"
                ),
                "tests": tests1,
                "ops": [("replace", "core.py", rule_old, rule_new)],
                "expect_targets": {"core.py"},
            },
            {
                "instruction": (
                    f"core.py 新增 {p['f_new']}(n)：返回 {p['f_rule']}(n) + {p['f_base']}(n)。"
                ),
                "tests": tests2,
                "ops": [("replace", "core.py", new_fn_old, new_fn_new)],
                "expect_targets": {"core.py"},
            },
        ],
        info_points=[
            {"id": "ip_spec", "type": "implementation",
             "value": f"return v * {m}",
             "locator": "instruction:step1 + core.py",
             "needed_by_steps": [1, 2],
             "redundant_in_instruction": True},
            {"id": "ip_history_rule", "type": "history",
             "value": f"v * {m}",
             "locator": "workspace core.py (step1 edit) + assistant history",
             "needed_by_steps": [2],
             "redundant_in_instruction": False},
        ],
    )

# ============================================================ SF2 依赖常量（hidden critical_data）
_SF2 = [
    dict(n="01", cfg="rates", cname="RATE", value=4, doc="Quote arithmetic",
         f_apply="apply_rate", f_pair="apply_pair", f_check="positive", tools="widen"),
    dict(n="02", cfg="factors", cname="FACTOR", value=5, doc="Batch factor math",
         f_apply="apply_factor", f_pair="factor_pair", f_check="positive", tools="shrink"),
    dict(n="03", cfg="weights", cname="WEIGHT", value=3, doc="Weighted totals",
         f_apply="apply_weight", f_pair="weight_pair", f_check="positive", tools="clampw"),
    dict(n="04", cfg="margins", cname="MARGIN_PCT", value=8, doc="Margin arithmetic",
         f_apply="apply_margin", f_pair="margin_pair", f_check="positive", tools="trim"),
]

for p in _SF2:
    engine = (
        f'"""{p["doc"]}"""\n'
        f'from {p["cfg"]} import {p["cname"]}\n\n\n'
        f'def {p["f_apply"]}(v):\n'
        f'    return v + {p["cname"]}\n\n\n'
        f'def {p["f_check"]}(v):\n'
        f'    return v > 0\n'
    )
    cfg = (
        f'"""{p["cfg"]} constants (no functions)."""\n\n'
        f'{p["cname"]} = {p["value"]}\n'
        f'LABEL = "{p["cfg"]}-v1"\n'
    )
    tools = (
        '"""Misc tools."""\n\n\n'
        f'def {p["tools"]}(x):\n'
        f'    return x if x > 0 else 0\n'
    )
    apply_old = f'def {p["f_apply"]}(v):\n    return v + {p["cname"]}\n'
    apply_new = f'def {p["f_apply"]}(v):\n    return v * {p["cname"]}\n'
    pair_old = f'def {p["f_check"]}(v):\n    return v > 0\n'
    pair_new = (
        f'def {p["f_check"]}(v):\n'
        f'    return v > 0\n\n\n'
        f'def {p["f_pair"]}(a, b):\n'
        f'    return {p["f_apply"]}(a) + {p["f_apply"]}(b)\n'
    )
    v = p["value"]
    tests1 = (
        "import engine\n\n\n"
        "def test_apply_uses_constant():\n"
        f"    assert engine.{p['f_apply']}(2) == {2 * v}\n"
        f"    assert engine.{p['f_apply']}(5) == {5 * v}\n\n\n"
        "def test_check_regression():\n"
        "    assert engine.%s(-1) is False\n" % p["f_check"]
    )
    tests2 = (
        "import engine\n\n\n"
        "def test_pair():\n"
        f"    assert engine.{p['f_pair']}(1, 2) == {1 * v} + {2 * v}\n\n\n"
        "def test_apply_regression():\n"
        f"    assert engine.{p['f_apply']}(3) == {3 * v}\n\n\n"
        "def test_check_regression():\n"
        f"    assert engine.{p['f_check']}(0) is False\n"
    )
    T(
        id=f"p1_S{p['n']}b",
        family="p1_short_dep",
        type="implicit_constant_dependency",
        difficulty="short",
        focus="常量值仅在依赖文件（无实现体）；hidden critical_data 预声明",
        files={"engine.py": engine, f"{p['cfg']}.py": cfg, "threads.py": tools},
        steps=[
            {
                "instruction": (
                    f"请修改 engine.py 中的 {p['f_apply']}(v)：结果应为相乘语义"
                    f"（当前实现为 v + {p['cname']}）。{p['cname']} 的当前取值记录在 {p['cfg']}.py。"
                ),
                "tests": tests1,
                "ops": [("replace", "engine.py", apply_old, apply_new)],
                "expect_targets": {"engine.py"},
            },
            {
                "instruction": (
                    f"engine.py 新增 {p['f_pair']}(a, b)：返回 {p['f_apply']}(a) + {p['f_apply']}(b)。"
                ),
                "tests": tests2,
                "ops": [("replace", "engine.py", pair_old, pair_new)],
                "expect_targets": {"engine.py"},
            },
        ],
        info_points=[
            {"id": "ip_constant_value", "type": "critical_data",
             "value": str(v),
             "locator": f"{p['cfg']}.py:{p['cname']}",
             "needed_by_steps": [1, 2],
             "redundant_in_instruction": False},
            {"id": "ip_engine_import", "type": "interface",
             "value": f"from {p['cfg']} import {p['cname']}",
             "locator": "engine.py header",
             "needed_by_steps": [1],
             "redundant_in_instruction": False},
        ],
    )

# ============================================================ SF3 弱命名双文件
_SF3 = [
    dict(n="01", a="routing", f="pick_route", spec="larger",
         fn2="normalize", inv="去掉首尾空白并转小写", inv_new='str(node).strip().lower()'),
    dict(n="02", a="packing", f="pick_pack", spec="larger",
         fn2="canon_label", inv="去除首尾空白并转大写", inv_new='str(node).strip().upper()'),
    dict(n="03", a="scoring", f="pick_rank", spec="larger",
         fn2="round_note", inv="四舍五入保留 1 位小数（转字符串）",
         inv_new='str(round(float(node), 1))'),
    dict(n="04", a="billing", f="pick_bill", spec="larger",
         fn2="tag_clean", inv="去掉首尾空白并加前缀 `ok:`",
         inv_new='"ok:" + str(node).strip()'),
]

for p in _SF3:
    main_f = (
        '"""Companion module (target)."""\n\n\n'
        f'def {p["f"]}(nodes):\n'
        f'    return sorted(nodes)[-1] if nodes else None\n\n\n'
        f'def summarize(nodes):\n'
        f'    return len(nodes)\n'
    )
    rules_f = (
        '"""Rules companion (ambiguity source)."""\n\n'
        'PRIORITY = 3\n\n\n'
        f'def {p["f"]}(nodes):\n'
        f'    # rule-flavored picker: returns the alphabetically smallest node\n'
        f'    return sorted(nodes)[0] if nodes else None\n\n\n'
        f'def {p["fn2"]}(node):\n'
        f'    return str(node)\n'
    )
    misc = (
        '"""Unrelated scratch."""\n\n\n'
        f'def stamp():\n'
        f'    return "{p["a"]}-stamp"\n'
    )
    # 规范：返回字母序最大者（rules 初始为最小 → 违反；主文件已合规）
    # 主文件 pick 返回 [-1]=最大 → 合规；规则文件返回 [0] → 违反规范 → 模型须改对文件
    tests1 = (
        f"from {p['a']} import {p['f']}\n"
        f"from {p['a']}_rules import {p['f']} as rules_{p['f']}\n\n\n"
        "def test_empty():\n"
        f"    assert {p['f']}([]) is None\n\n\n"
        "def test_target_returns_largest():\n"
        f"    assert {p['f']}(['b', 'a', 'c']) == 'c'\n\n\n"
        "def test_rules_companion_also_largest():\n"
        f"    assert rules_{p['f']}(['b', 'a', 'c']) == 'c'\n"
    )
    tests2 = (
        f"from {p['a']}_rules import {p['fn2']}, {p['f']} as rp\n\n\n"
        f"def test_fn2():\n"
        f"    assert {p['fn2']}('  xy  ') == {p['inv_new']!r}.replace('  xy  ', '  xy  ')\n\n\n"
        "def test_picker_regression():\n"
        "    assert rp(['b', 'a', 'c']) == 'c'\n"
    )
    # 上面 tests2 的写法过于绕——改为直接按变体生成明确断言
    inv_assert = {
        "01": "assert {fn2}('  xy  ') == 'xy'",
        "02": "assert {fn2}('  xy  ') == 'XY'",
        "03": "assert {fn2}('3.14159') == '3.1'",
        "04": "assert {fn2}('  xy  ') == 'ok:xy'",
    }[p["n"]].format(fn2=p["fn2"])
    tests2 = (
        f"from {p['a']}_rules import {p['fn2']}\n"
        f"from {p['a']} import {p['f']}\n\n\n"
        "def test_fn2_spec():\n"
        f"    {inv_assert}\n\n\n"
        "def test_picker_regression():\n"
        f"    assert {p['f']}(['b', 'a', 'c']) == 'c'\n"
    )
    T(
        id=f"p1_S{p['n']}c",
        family="p1_short_naming",
        type="weak_naming_ambiguity",
        difficulty="short",
        focus="同名符号跨两文件；指令不给路径（符号歧义 → 双文件全量）",
        files={
            f"{p['a']}.py": main_f,
            f"{p['a']}_rules.py": rules_f,
            "scratchpad.py": misc,
        },
        steps=[
            {
                "instruction": (
                    f"请修改 {p['f']}(nodes)：无节点应返回 None，有节点应按字母序返回最大节点"
                    f"（当前某处实现有误，涉及 {p['a']} 相关模块）。"
                ),
                "tests": tests1,
                "ops": [
                    ("replace", f"{p['a']}_rules.py",
                     f'def {p["f"]}(nodes):\n'
                     f'    # rule-flavored picker: returns the alphabetically smallest node\n'
                     f'    return sorted(nodes)[0] if nodes else None\n',
                     f'def {p["f"]}(nodes):\n'
                     f'    # rule-flavored picker: returns the alphabetically largest node\n'
                     f'    return sorted(nodes)[-1] if nodes else None\n'),
                ],
                "expect_targets": {f"{p['a']}.py", f"{p['a']}_rules.py"},
            },
            {
                "instruction": (
                    f"{p['a']}_rules.py 中的 {p['fn2']}(node) 应{p['inv']}（当前原样返回）。"
                ),
                "tests": tests2,
                "ops": [
                    ("replace", f"{p['a']}_rules.py",
                     f'def {p["fn2"]}(node):\n    return str(node)\n',
                     f'def {p["fn2"]}(node):\n    return {p["inv_new"]}\n'),
                ],
                "expect_targets": {f"{p['a']}_rules.py"},
            },
        ],
        info_points=[
            {"id": "ip_symbol_scope", "type": "interface",
             "value": f"{p['f']}(",
             "locator": f"both {p['a']}*.py",
             "needed_by_steps": [1],
             "redundant_in_instruction": True},
            {"id": "ip_rules_file_path", "type": "critical_data",
             "value": f"{p['a']}_rules.py",
             "locator": "instruction:step2",
             "needed_by_steps": [2],
             "redundant_in_instruction": True},
        ],
    )

# ============================================================ SF4 类契约
_SF4 = [
    dict(n="01", cls="Reserve", f="withdraw", f2="drain_view", vault_doc="Reserve accounts",
         acct_doc="Reporting side", init=100, amt=30),
    dict(n="02", cls="Session", f="consume", f2="burn_view", vault_doc="Session tokens",
         acct_doc="Session stats", init=50, amt=20),
    dict(n="03", cls="Deposit", f="takeout", f2="peek_view", vault_doc="Deposit slips",
         acct_doc="Deposit reports", init=80, amt=25),
    dict(n="04", cls="Loan", f="repay", f2="due_view", vault_doc="Loan books",
         acct_doc="Loan summaries", init=120, amt=40),
]

for p in _SF4:
    vault = (
        f'"""{p["vault_doc"]}"""\n\n\n'
        f'class {p["cls"]}:\n'
        f'    def __init__(self, balance):\n'
        f'        self.balance = balance\n\n'
        f'    def {p["f"]}(self, amount):\n'
        f'        self.balance -= amount\n'
        f'        return self.balance\n\n'
        f'    def report(self):\n'
        f'        return "acct:" + str(self.balance)\n'
    )
    acct = (
        f'"""{p["acct_doc"]}"""\n\n\n'
        f'def total_line(balance):\n'
        f'    return f"total: {{balance}}"\n'
    )
    catalog = (
        '"""Unrelated catalog."""\n\n\n'
        'def names():\n'
        '    return ["a", "b"]\n'
    )
    w_old = f'    def {p["f"]}(self, amount):\n        self.balance -= amount\n        return self.balance\n'
    w_new = (
        f'    def {p["f"]}(self, amount):\n'
        f'        if amount <= 0:\n'
        f'            raise ValueError("amount must be positive")\n'
        f'        self.balance -= amount\n'
        f'        return self.balance\n'
    )
    view_old = 'def total_line(balance):\n    return f"total: {balance}"\n'
    view_new = (
        'def total_line(balance):\n'
        '    return f"total: {balance}"\n\n\n'
        f'def {p["f2"]}(account, amount):\n'
        f'    return account.{p["f"]}(amount)\n'
    )
    tests1 = (
        "import pytest\n"
        f"from vault import {p['cls']}\n\n\n"
        "def test_positive_ok():\n"
        f"    a = {p['cls']}({p['init']})\n"
        f"    assert a.{p['f']}({p['amt']}) == {p['init'] - p['amt']}\n\n\n"
        "def test_zero_raises():\n"
        f"    a = {p['cls']}({p['init']})\n"
        f"    with pytest.raises(ValueError):\n"
        f"        a.{p['f']}(0)\n\n\n"
        "def test_negative_raises():\n"
        f"    a = {p['cls']}({p['init']})\n"
        f"    with pytest.raises(ValueError):\n"
        f"        a.{p['f']}(-5)\n"
    )
    tests2 = (
        "import pytest\n"
        f"from vault import {p['cls']}\n"
        f"from accounting import {p['f2']}\n\n\n"
        "def test_view_ok():\n"
        f"    a = {p['cls']}({p['init']})\n"
        f"    assert {p['f2']}(a, {p['amt']}) == {p['init'] - p['amt']}\n\n\n"
        "def test_view_propagates():\n"
        f"    a = {p['cls']}({p['init']})\n"
        "    with pytest.raises(ValueError):\n"
        f"        {p['f2']}(a, 0)\n\n\n"
        "def test_contract_regression():\n"
        f"    a = {p['cls']}({p['init']})\n"
        "    with pytest.raises(ValueError):\n"
        f"        a.{p['f']}(-1)\n"
    )
    T(
        id=f"p1_S{p['n']}d",
        family="p1_short_contract",
        type="class_contract",
        difficulty="short",
        focus="类契约收紧 + 消费方传播（含跨文件回归）",
        files={"vault.py": vault, "accounting.py": acct, "catalog.py": catalog},
        steps=[
            {
                "instruction": (
                    f"请修改 vault.py 中的 {p['cls']}.{p['f']}(amount)："
                    f"amount ≤ 0 应抛 ValueError（当前接受任意 amount）。"
                ),
                "tests": tests1,
                "ops": [("replace", "vault.py", w_old, w_new)],
                "expect_targets": {"vault.py"},
            },
            {
                "instruction": (
                    f"accounting.py 新增 {p['f2']}(account, amount)："
                    f"对 account 调用 {p['f']}(amount) 并返回其余额；非法 amount 应整体抛 ValueError。"
                ),
                "tests": tests2,
                "ops": [("replace", "accounting.py", view_old, view_new)],
                "expect_targets": {"accounting.py"},
            },
        ],
        info_points=[
            {"id": "ip_contract_rule", "type": "implementation",
             "value": "raise ValueError",
             "locator": "instruction:step1 + vault.py",
             "needed_by_steps": [1, 2],
             "redundant_in_instruction": True},
            {"id": "ip_method_name", "type": "history",
             "value": f"{p['f']}(self, amount)",
             "locator": "vault.py method via assistant history (step1 FILE block)",
             "needed_by_steps": [2],
             "redundant_in_instruction": True},
        ],
    )
