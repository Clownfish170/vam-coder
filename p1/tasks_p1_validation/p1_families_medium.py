"""P1 Medium 族（2 族 × 8 变体 = 16 题，每题 5 步）。由 make_p1_tasks 导入注册。"""

from p1_registry import T

# ============================================================ MA 特性累积链（跨文件）
_MA = [
    dict(n="01", inv="Inventory ledger", pri="Price sheet", cat="Catalog side",
         f_avail="available", f_cnt="count_rows", f_res="reserve", unit=7,
         f_settle="settle", f_list="settle_list", f_cat="cat_tag", tag="inv-a"),
    dict(n="02", inv="Stock tracking", pri="Unit pricing", cat="Stock notes",
         f_avail="net_of", f_cnt="tally", f_res="hold", unit=9,
         f_settle="quote_held", f_list="quote_batch", f_cat="stock_tag", tag="stk-b"),
    dict(n="03", inv="Shelf counts", pri="Shelf rates", cat="Shelf meta",
         f_avail="free_qty", f_cnt="rows_seen", f_res="park", unit=6,
         f_settle="parked_price", f_list="parked_many", f_cat="shelf_tag", tag="shf-c"),
    dict(n="04", inv="Bin levels", pri="Bin charges", cat="Bin notes",
         f_avail="open_slots", f_cnt="bin_count", f_res="block", unit=8,
         f_settle="billed", f_list="billed_all", f_cat="bin_tag", tag="bin-d"),
    dict(n="05", inv="Pool meters", pri="Pool rates", cat="Pool log",
         f_avail="net_flow", f_cnt="log_rows", f_res="dial", unit=11,
         f_settle="flow_bill", f_list="flow_bills", f_cat="pool_tag", tag="poo-e"),
    dict(n="06", inv="Queue counts", pri="Queue fees", cat="Queue misc",
         f_avail="open_count", f_cnt="queue_len", f_res="seat", unit=12,
         f_settle="seated_fee", f_list="seated_fees", f_cat="queue_tag", tag="que-f"),
    dict(n="07", inv="Cache entries", pri="Cache tariffs", cat="Cache notes",
         f_avail="warm_slots", f_cnt="entry_no", f_res="pin", unit=5,
         f_settle="pinned_rate", f_list="pinned_rates", f_cat="cache_tag", tag="cac-g"),
    dict(n="08", inv="Lane usage", pri="Lane prices", cat="Lane notes",
         f_avail="open_lanes", f_cnt="lane_rows", f_res="book", unit=4,
         f_settle="booked_price", f_list="booked_prices", f_cat="lane_tag", tag="lan-h"),
]

for p in _MA:
    inv = (
        f'"""{p["inv"]}"""\n\n'
        'LEDGER = {}\n\n\n'
        f'def {p["f_avail"]}(qty, held):\n'
        f'    return qty\n\n\n'
        f'def {p["f_cnt"]}(rows):\n'
        f'    return len(rows)\n'
    )
    pri = (
        f'"""{p["pri"]}"""\n\n'
        f'UNIT = {p["unit"]}\n\n\n'
        f'def price_of(qty):\n'
        f'    return qty * UNIT\n'
    )
    cat = (
        f'"""{p["cat"]}"""\n\n\n'
        f'def {p["f_cat"]}():\n'
        f'    return "{p["tag"]}"\n'
    )
    a1_old = f'def {p["f_avail"]}(qty, held):\n    return qty\n'
    a1_new = f'def {p["f_avail"]}(qty, held):\n    return qty - held\n'
    a2_old = 'LEDGER = {}\n'
    a2_new = (
        'LEDGER = {}\n\n\n'
        f'def {p["f_res"]}(k, n):\n'
        f'    LEDGER.setdefault(k, []).append(n)\n'
        f'    return LEDGER[k]\n'
    )
    s3_old = 'def price_of(qty):\n    return qty * UNIT\n'
    s3_new = (
        f'def price_of(qty):\n'
        f'    return qty * UNIT\n\n\n'
        f'def {p["f_settle"]}(qty, held):\n'
        f'    return {p["f_avail"]}(qty, held) * UNIT\n'
    )
    # step3 需要在文件顶部加 import → 用 replace 在 docstring 行后插入
    s3_import_anchor = f'"""{p["pri"]}"""\n\n'
    s3_import_new = f'"""{p["pri"]}"""\nfrom inventory import {p["f_avail"]}\n\n'
    a4_old = f'def {p["f_avail"]}(qty, held):\n    return qty - held\n'
    a4_new = (
        f'def {p["f_avail"]}(qty, held):\n'
        f'    net = qty - held\n'
        f'    return net if net > 0 else 0\n'
    )
    s5_old = f'def {p["f_settle"]}(qty, held):\n    return {p["f_avail"]}(qty, held) * UNIT\n'
    s5_new = (
        f'def {p["f_settle"]}(qty, held):\n'
        f'    return {p["f_avail"]}(qty, held) * UNIT\n\n\n'
        f'def {p["f_list"]}(pairs):\n'
        f'    return [{p["f_settle"]}(q, h) for q, h in pairs]\n'
    )
    u = p["unit"]
    tests1 = (
        "import inventory\n\n\n"
        "def test_net():\n"
        f"    assert inventory.{p['f_avail']}(10, 3) == 7\n"
        f"    assert inventory.{p['f_avail']}(5, 0) == 5\n\n\n"
        "def test_count_regression():\n"
        f"    assert inventory.{p['f_cnt']}(['x', 'y']) == 2\n"
    )
    tests2 = (
        "import inventory\n\n\n"
        "def test_reserve_ledger():\n"
        f"    assert inventory.{p['f_res']}('a', 1) == [1]\n"
        f"    assert inventory.{p['f_res']}('a', 2) == [1, 2]\n\n\n"
        "def test_avail_regression():\n"
        f"    assert inventory.{p['f_avail']}(10, 3) == 7\n"
    )
    tests3 = (
        "import pricing\n"
        "from inventory import " + p["f_avail"] + "\n\n\n"
        "def test_settle():\n"
        f"    assert pricing.{p['f_settle']}(10, 3) == 7 * {u}\n"
        f"    assert pricing.{p['f_settle']}(6, 1) == 5 * {u}\n\n\n"
        "def test_avail_visible():\n"
        f"    assert {p['f_avail']}(10, 3) == 7\n\n\n"
        "def test_price_regression():\n"
        f"    assert pricing.price_of(2) == {2 * u}\n"
    )
    tests4 = (
        "import inventory\n"
        "import pricing\n\n\n"
        "def test_clamp_negative():\n"
        f"    assert inventory.{p['f_avail']}(4, 5) == 0\n"
        f"    assert inventory.{p['f_avail']}(4, 1) == 3\n\n\n"
        "def test_settle_regression():\n"
        f"    assert pricing.{p['f_settle']}(10, 3) == 7 * {u}\n"
        f"    assert pricing.{p['f_settle']}(4, 5) == 0\n\n\n"
        "def test_reserve_regression():\n"
        f"    assert inventory.{p['f_res']}('b', 1) == [1]\n"
    )
    tests5 = (
        "import pricing\n\n\n"
        "def test_settle_list():\n"
        f"    assert pricing.{p['f_list']}([(10, 3), (4, 5)]) == [7 * {u}, 0]\n"
        f"    assert pricing.{p['f_list']}([]) == []\n\n\n"
        "def test_settle_regression():\n"
        f"    assert pricing.{p['f_settle']}(10, 3) == 7 * {u}\n\n\n"
        "def test_price_regression():\n"
        f"    assert pricing.price_of(3) == {3 * u}\n"
    )
    T(
        id=f"p1_M{p['n']}a",
        family="p1_medium_feature_chain",
        type="cross_module_feature_accumulation",
        difficulty="medium",
        focus="5 步跨文件特性链：结构→跨模块组合→边界回归→批量",
        files={"inventory.py": inv, "pricing.py": pri, "catalog.py": cat},
        steps=[
            {
                "instruction": (
                    f"请修改 inventory.py 中的 {p['f_avail']}(qty, held)："
                    f"应返回 qty − held（当前返回 qty）。"
                ),
                "tests": tests1,
                "ops": [("replace", "inventory.py", a1_old, a1_new)],
                "expect_targets": {"inventory.py"},
            },
            {
                "instruction": (
                    f"inventory.py 新增 {p['f_res']}(k, n)：把 n 追加到 LEDGER[k]"
                    f"（键不存在则先建空列表），并返回该列表。"
                ),
                "tests": tests2,
                "ops": [("replace", "inventory.py", a2_old, a2_new)],
                "expect_targets": {"inventory.py"},
            },
            {
                "instruction": (
                    f"pricing.py 新增 {p['f_settle']}(qty, held)：净量 × UNIT，结果为整数。"
                    f"净量口径在 inventory.py 的 {p['f_avail']}。"
                ),
                "tests": tests3,
                "ops": [
                    ("replace", "pricing.py", s3_import_anchor, s3_import_new),
                    ("replace", "pricing.py", s3_old, s3_new),
                ],
                "expect_targets": {"pricing.py"},
            },
            {
                "instruction": (
                    f"inventory.py 中的 {p['f_avail']}(qty, held)："
                    f"净量为负时应返回 0（其他行为保持不变）。"
                ),
                "tests": tests4,
                "ops": [("replace", "inventory.py", a4_old, a4_new)],
                "expect_targets": {"inventory.py"},
            },
            {
                "instruction": (
                    f"pricing.py 新增 {p['f_list']}(pairs)：对每对 (qty, held) 调用 "
                    f"{p['f_settle']} 并返回结果列表（空输入返回 []）。"
                ),
                "tests": tests5,
                "ops": [("replace", "pricing.py", s5_old, s5_new)],
                "expect_targets": {"pricing.py"},
            },
        ],
        info_points=[
            {"id": "ip_avail_semantics", "type": "implementation",
             "value": "qty - held",
             "locator": "inventory.py (after step1) + assistant history",
             "needed_by_steps": [3, 4],
             "redundant_in_instruction": False},
            {"id": "ip_unit_value", "type": "critical_data",
             "value": str(u),
             "locator": "pricing.py:UNIT",
             "needed_by_steps": [3, 5],
             "redundant_in_instruction": False},
            {"id": "ip_ledger_struct", "type": "interface",
             "value": "LEDGER",
             "locator": "instruction:step2 + inventory.py",
             "needed_by_steps": [2, 4],
             "redundant_in_instruction": True},
        ],
    )

# ============================================================ MB 接口演进链
_MB = [
    dict(n="01", impl_doc="Render pipeline", api_doc="Public api",
         ad_doc="Adapter extras", f_render="render", f_call="call", f_via="render_via",
         f_wrap="wrap_one", initial_sep="|"),
    dict(n="02", impl_doc="Line formatter", api_doc="Service facade",
         ad_doc="Side adapters", f_render="emit", f_call="invoke", f_via="emit_via",
         f_wrap="wrap_one", initial_sep="~"),
    dict(n="03", impl_doc="Text joiner", api_doc="Outer layer",
         ad_doc="Extra layer", f_render="join_items", f_call="run_join", f_via="join_via",
         f_wrap="wrap_item", initial_sep="#"),
    dict(n="04", impl_doc="Row writer", api_doc="Entry facade",
         ad_doc="Entry extras", f_render="write_row", f_call="send", f_via="write_via",
         f_wrap="wrap_row", initial_sep="@"),
    dict(n="05", impl_doc="Stream printer", api_doc="Stream api",
         ad_doc="Stream extras", f_render="print_stream", f_call="push", f_via="print_via",
         f_wrap="wrap_push", initial_sep="|"),
    dict(n="06", impl_doc="Cell join core", api_doc="Cell api",
         ad_doc="Cell extras", f_render="join_cells", f_call="open_cells", f_via="cells_via",
         f_wrap="wrap_cell", initial_sep="%"),
    dict(n="07", impl_doc="Row glue", api_doc="Glue facade",
         ad_doc="Glue extras", f_render="glue", f_call="glue_call", f_via="glue_via",
         f_wrap="wrap_glue", initial_sep="="),
    dict(n="08", impl_doc="Seq builder", api_doc="Seq facade",
         ad_doc="Seq extras", f_render="build_seq", f_call="seq_run", f_via="seq_via",
         f_wrap="wrap_seq", initial_sep="+"),
]

for p in _MB:
    impl = (
        f'"""{p["impl_doc"]}"""\n\n\n'
        f'def {p["f_render"]}(data):\n'
        f'    return "{p["initial_sep"]}".join(str(x) for x in data)\n'
    )
    api = (
        f'"""{p["api_doc"]}"""\n'
        f'from impl import {p["f_render"]}\n\n\n'
        f'def {p["f_call"]}(data):\n'
        f'    return {p["f_render"]}(data)\n'
    )
    adapter = (
        f'"""{p["ad_doc"]}"""\n\n\n'
        f'def {p["f_wrap"]}(x):\n'
        f'    return [x]\n'
    )
    scratch = (
        '"""Unrelated scratch."""\n\n\n'
        'def noise():\n'
        '    return "noise"\n'
    )
    r1_old = (
        f'def {p["f_render"]}(data):\n'
        f'    return "{p["initial_sep"]}".join(str(x) for x in data)\n'
    )
    r1_new = (
        f'def {p["f_render"]}(data):\n'
        f'    return ", ".join(str(x) for x in data)\n'
    )
    r2_old = r1_new
    r2_new = (
        f'def {p["f_render"]}(data, sep=", "):\n'
        f'    return sep.join(str(x) for x in data)\n'
    )
    c_old = (
        f'def {p["f_call"]}(data):\n'
        f'    return {p["f_render"]}(data)\n'
    )
    c_new = (
        f'def {p["f_call"]}(data, sep=None):\n'
        f'    if sep is None:\n'
        f'        return {p["f_render"]}(data)\n'
        f'    return {p["f_render"]}(data, sep)\n'
    )
    w_old = f'def {p["f_wrap"]}(x):\n    return [x]\n'
    w_new = (
        f'def {p["f_wrap"]}(x):\n'
        f'    return [x]\n\n\n'
        f'def {p["f_via"]}(data):\n'
        f'    return {p["f_render"]}(data, "-")\n'
    )
    w_import_anchor = f'"""{p["ad_doc"]}"""\n\n'
    w_import_new = f'"""{p["ad_doc"]}"""\nfrom impl import {p["f_render"]}\n\n'
    r3_old = (
        f'def {p["f_render"]}(data, sep=", "):\n'
        f'    return sep.join(str(x) for x in data)\n'
    )
    r3_new = (
        f'def {p["f_render"]}(data, sep=", "):\n'
        f'    items = [str(x) for x in data if x is not None]\n'
        f'    return sep.join(items)\n'
    )
    tests1 = (
        f"from impl import {p['f_render']}\n\n\n"
        "def test_separator():\n"
        f"    assert {p['f_render']}(['a', 'b']) == 'a, b'\n"
        f"    assert {p['f_render']}(['x']) == 'x'\n"
    )
    tests2 = (
        f"from impl import {p['f_render']}\n\n\n"
        "def test_default_sep():\n"
        f"    assert {p['f_render']}(['a', 'b']) == 'a, b'\n\n\n"
        "def test_explicit_sep():\n"
        f"    assert {p['f_render']}(['a', 'b'], ';') == 'a;b'\n"
    )
    tests3 = (
        f"from impl import {p['f_render']}\n"
        f"from api import {p['f_call']}\n\n\n"
        "def test_call_default():\n"
        f"    assert {p['f_call']}(['a', 'b']) == 'a, b'\n\n\n"
        "def test_call_with_sep():\n"
        f"    assert {p['f_call']}(['a', 'b'], ';') == 'a;b'\n\n\n"
        "def test_render_regression():\n"
        f"    assert {p['f_render']}(['q'], '|') == 'q'\n"
    )
    tests4 = (
        f"from impl import {p['f_render']}\n"
        f"from api import {p['f_call']}\n"
        f"from adapter import {p['f_via']}\n\n\n"
        "def test_via_dash():\n"
        f"    assert {p['f_via']}(['x', 'y']) == 'x-y'\n\n\n"
        "def test_call_regression():\n"
        f"    assert {p['f_call']}(['a', 'b'], ';') == 'a;b'\n\n\n"
        "def test_render_regression():\n"
        f"    assert {p['f_render']}(['a', 'b']) == 'a, b'\n"
    )
    tests5 = (
        f"from impl import {p['f_render']}\n"
        f"from api import {p['f_call']}\n"
        f"from adapter import {p['f_via']}\n\n\n"
        "def test_none_filtered():\n"
        f"    assert {p['f_render']}(['a', None, 'b']) == 'a, b'\n\n\n"
        "def test_explicit_sep_filtered():\n"
        f"    assert {p['f_render']}(['a', None, 'b'], ';') == 'a;b'\n\n\n"
        "def test_chain_regressions():\n"
        f"    assert {p['f_call']}(['a', 'b'], ';') == 'a;b'\n"
        f"    assert {p['f_via']}(['x', 'y']) == 'x-y'\n"
        f"    assert {p['f_render']}([]) == ''\n"
    )
    T(
        id=f"p1_M{p['n']}b",
        family="p1_medium_interface_evolution",
        type="interface_change_chain",
        difficulty="medium",
        focus="5 步接口演进：规格→签名扩展→调用方同步→新消费方→边界",
        files={
            "impl.py": impl, "api.py": api, "adapter.py": adapter, "scratch.py": scratch,
        },
        steps=[
            {
                "instruction": (
                    f"请修改 impl.py 中的 {p['f_render']}(data)："
                    f'分隔符应为 ", "（当前为 "{p["initial_sep"]}")。'
                ),
                "tests": tests1,
                "ops": [("replace", "impl.py", r1_old, r1_new)],
                "expect_targets": {"impl.py"},
            },
            {
                "instruction": (
                    f"impl.py 中的 {p['f_render']} 必须新增参数 sep，默认 \", \"："
                    f"调用方可传入其他分隔符（当前签名不含 sep）。"
                ),
                "tests": tests2,
                "ops": [("replace", "impl.py", r2_old, r2_new)],
                "expect_targets": {"impl.py"},
            },
            {
                "instruction": (
                    f"api.py 同步：{p['f_call']} 增加参数 sep=None，"
                    f"不为 None 时透传给 {p['f_render']}（当前 {p['f_call']} 不支持 sep）。"
                ),
                "tests": tests3,
                "ops": [("replace", "api.py", c_old, c_new)],
                "expect_targets": {"api.py", "impl.py"},
            },
            {
                "instruction": (
                    f"adapter.py 新增 {p['f_via']}(data)：以 \"-\" 为分隔符调用 "
                    f"impl.{p['f_render']}（需要补充 import）。"
                ),
                "tests": tests4,
                "ops": [
                    ("replace", "adapter.py", w_import_anchor, w_import_new),
                    ("replace", "adapter.py", w_old, w_new),
                ],
                "expect_targets": {"adapter.py", "impl.py"},
            },
            {
                "instruction": (
                    f"请修改 impl.py 中的 {p['f_render']}：data 中的 None 元素应被跳过"
                    f"（其他行为与既有 sep 语义保持不变）。"
                ),
                "tests": tests5,
                "ops": [("replace", "impl.py", r3_old, r3_new)],
                "expect_targets": {"impl.py"},
            },
        ],
        info_points=[
            {"id": "ip_sep_default", "type": "critical_data",
             "value": '", "',
             "locator": "instruction:step1 + impl.py",
             "needed_by_steps": [1, 2, 3],
             "redundant_in_instruction": True},
            {"id": "ip_render_signature", "type": "history",
             "value": f"{p['f_render']}(data, sep",
             "locator": "impl.py (step2) via workspace + assistant history",
             "needed_by_steps": [3, 4],
             "redundant_in_instruction": True},
            {"id": "ip_call_passthrough", "type": "implementation",
             "value": f"{p['f_render']}(data, sep)",
             "locator": "api.py (step3)",
             "needed_by_steps": [4, 5],
             "redundant_in_instruction": False},
        ],
    )
