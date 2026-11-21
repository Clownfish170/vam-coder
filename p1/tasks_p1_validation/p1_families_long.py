"""P1 Long 族（2 族 × 8 变体 = 16 题，每题 10 步）。由 make_p1_tasks 导入注册。"""

from p1_registry import T

# ============================================================ LA 系统演进链（10 步）
_LA = [
    dict(n="01", hub="Billing hub", store="Fee store", pol="Fee policy",
         rep="Fee report", misc="Side notes",
         fq="quote", ft="trim", fp="put", fg="get", fm="merge",
         fc="ok_limit", fl="line", fr="run", fs="summary", fcap="cap_fee",
         wrong="qty + 5", mult=3, v0=100, v1=250, v2=400, tag="hub-a"),
    dict(n="02", hub="Rate core", store="Rate log", pol="Rate caps",
         rep="Rate lines", misc="Rate notes",
         fq="price", ft="clean", fp="save", fg="load", fm="blend",
         fc="under_cap", fl="fmt", fr="show", fs="show_many", fcap="apply_cap",
         wrong="qty - 3", mult=4, v0=150, v1=300, v2=500, tag="rate-b"),
    dict(n="03", hub="Margin hub", store="Margin store", pol="Margin policy",
         rep="Margin report", misc="Margin misc",
         fq="scale", ft="norm", fp="record", fg="fetch", fm="fold",
         fc="within", fl="row", fr="emit", fs="emit_all", fcap="bound",
         wrong="qty * 9", mult=2, v0=80, v1=200, v2=350, tag="mrg-c"),
    dict(n="04", hub="Ticket core", store="Ticket ledger", pol="Ticket rules",
         rep="Ticket lines", misc="Ticket scratch",
         fq="cost", ft="tidy", fp="add", fg="peek", fm="join",
         fc="rule_ok", fl="entry", fr="entry_of", fs="entries", fcap="clamp_cost",
         wrong="qty + 10", mult=5, v0=120, v1=280, v2=450, tag="tkt-d"),
    dict(n="05", hub="Grade hub", store="Grade store", pol="Grade caps",
         rep="Grade report", misc="Grade notes",
         fq="points", ft="fix", fp="put_row", fg="get_row", fm="merge_rows",
         fc="cap_ok", fl="label", fr="label_for", fs="labels", fcap="cap_pts",
         wrong="qty - 7", mult=6, v0=90, v1=220, v2=380, tag="grd-e"),
    dict(n="06", hub="Rent hub", store="Rent log", pol="Rent policy",
         rep="Rent report", misc="Rent misc",
         fq="fee_of", ft="scrub", fp="log", fg="last", fm="combine",
         fc="allowed", fl="desc", fr="desc_of", fs="descs", fcap="cap_rent",
         wrong="qty + 2", mult=3, v0=110, v1=260, v2=420, tag="rnt-f"),
    dict(n="07", hub="Loan hub", store="Loan store", pol="Loan caps",
         rep="Loan report", misc="Loan notes",
         fq="interest", ft="tidy_i", fp="save_i", fg="load_i", fm="merge_i",
         fc="within_i", fl="line_i", fr="line_of", fs="lines_of", fcap="cap_interest",
         wrong="qty * 11", mult=2, v0=140, v1=320, v2=480, tag="ln-g"),
    dict(n="08", hub="Tax hub", store="Tax store", pol="Tax policy",
         rep="Tax report", misc="Tax notes",
         fq="compute", ft="fix_tax", fp="put_tax", fg="get_tax", fm="merge_tax",
         fc="tax_ok", fl="tax_line", fr="tax_run", fs="tax_all", fcap="cap_tax",
         wrong="qty + 8", mult=4, v0=130, v1=290, v2=460, tag="tax-h"),
]

for p in _LA:
    hub = (
        f'"""{p["hub"]}"""\n\n\n'
        f'def {p["fq"]}(qty):\n'
        f'    return {p["wrong"]}\n\n\n'
        f'def {p["ft"]}(x):\n'
        f'    return x\n'
    )
    store = (
        f'"""{p["store"]}"""\n\n'
        'DATA = {}\n\n\n'
        f'def {p["fp"]}(k, v):\n'
        f'    DATA[k] = v\n'
        f'    return DATA\n\n\n'
        f'def {p["fg"]}(k):\n'
        f'    return DATA.get(k)\n'
    )
    pol = (
        f'"""{p["pol"]}"""\n\n'
        f'LIMIT = {p["v0"]}\n\n\n'
        f'def {p["fc"]}(fee):\n'
        f'    return fee <= LIMIT\n'
    )
    rep = (
        f'"""{p["rep"]}"""\n\n\n'
        f'def {p["fl"]}(fee):\n'
        f'    return f"fee: {{fee}}"\n'
    )
    misc = (
        f'"""{p["misc"]}"""\n\n\n'
        f'def {p["fr"] if False else "side_tag"}():\n'
        f'    return "{p["tag"]}"\n'
    )
    # ---- step ops（锚点均来自同参数生成的前序状态）
    s1_old = f'def {p["fq"]}(qty):\n    return {p["wrong"]}\n'
    s1_new = (
        f'def {p["fq"]}(qty):\n'
        f'    if qty < 0:\n'
        f'        return 0\n'
        f'    return qty * {p["mult"]}\n'
    )
    s2a_old = 'DATA = {}\n'
    s2a_new = 'DATA = {}\nLOG = {}\n'
    s2b_old = f'def {p["fp"]}(k, v):\n    DATA[k] = v\n    return DATA\n'
    s2b_new = (
        f'def {p["fp"]}(k, v):\n'
        f'    DATA[k] = v\n'
        f'    LOG.setdefault(k, []).append(v)\n'
        f'    return DATA\n'
    )
    s3_old = f'LIMIT = {p["v0"]}\n'
    s3_new = f'LIMIT = {p["v1"]}\n'
    s4_old = f'def {p["ft"]}(x):\n    return x\n'
    s4_new = f'def {p["ft"]}(x):\n    if x is None:\n        return "-"\n    return x\n'
    s5a_old = f'"""{p["rep"]}"""\n\n'
    s5a_new = f'"""{p["rep"]}"""\nfrom hub import {p["fq"]}\n\n'
    s5b_old = f'def {p["fl"]}(fee):\n    return f"fee: {{fee}}"\n'
    s5b_new = (
        f'def {p["fl"]}(fee):\n'
        f'    return f"fee: {{fee}}"\n\n\n'
        f'def {p["fr"]}(qty):\n'
        f'    return {p["fl"]}({p["fq"]}(qty))\n'
    )
    s6_old = f'def {p["fg"]}(k):\n    return DATA.get(k)\n'
    s6_new = (
        f'def {p["fg"]}(k):\n'
        f'    return DATA.get(k)\n\n\n'
        f'def {p["fm"]}(other):\n'
        f'    DATA.update(other)\n'
        f'    return DATA\n'
    )
    s7a_old = f'"""{p["hub"]}"""\n\n'
    s7a_new = f'"""{p["hub"]}"""\nfrom policy import LIMIT\n\n'
    s7b_old = s4_new  # s4 之后的 trim 块
    s7b_new = (
        s4_new + '\n\n'
        f'def {p["fcap"]}(fee):\n'
        f'    return fee if fee <= LIMIT else LIMIT\n'
    )
    s8a_old = f'"""{p["rep"]}"""\nfrom hub import {p["fq"]}\n\n'
    s8a_new = (
        f'"""{p["rep"]}"""\n'
        f'from hub import {p["fq"]}\n'
        f'from hub import {p["fcap"]}\n\n'
    )
    s8b_old = f'def {p["fr"]}(qty):\n    return {p["fl"]}({p["fq"]}(qty))\n'
    s8b_new = (
        f'def {p["fr"]}(qty):\n'
        f'    return {p["fl"]}({p["fq"]}(qty))\n\n\n'
        f'def {p["fs"]}(fees):\n'
        f'    return [{p["fl"]}({p["fcap"]}(f)) for f in fees]\n'
    )
    s9_old = (
        f'def {p["fcap"]}(fee):\n'
        f'    return fee if fee <= LIMIT else LIMIT\n'
    )
    s9_new = (
        f'def {p["fcap"]}(fee):\n'
        f'    if fee < 0:\n'
        f'        return 0\n'
        f'    return fee if fee <= LIMIT else LIMIT\n'
    )
    s10_old = f'LIMIT = {p["v1"]}\n'
    s10_new = f'LIMIT = {p["v2"]}\n'
    mu, v1, v2 = p["mult"], p["v1"], p["v2"]

    def _t(i):
        # 每步 eval：新行为 + 关键回归（cumulative）
        base_q = (
            "import hub\n\n\n"
            "def test_quote():\n"
            f"    assert hub.{p['fq']}(-2) == 0\n"
            f"    assert hub.{p['fq']}(3) == {3 * mu}\n"
        )
        if i == 1:
            return base_q + f"    assert hub.{p['fq']}(0) == 0\n"
        if i == 2:
            return (
                "import hub\nimport store\n\n\n"
                "def test_put_logs():\n"
                f"    assert store.{p['fp']}('a', 1) is store.DATA\n"
                f"    assert store.LOG['a'] == [1]\n"
                f"    assert store.{p['fp']}('a', 2) is store.DATA\n"
                f"    assert store.LOG['a'] == [1, 2]\n\n\n"
                "def test_quote_regression():\n"
                f"    assert hub.{p['fq']}(3) == {3 * mu}\n"
            )
        if i == 3:
            return (
                f"import hub\nimport store\nimport policy\n\n\n"
                "def test_limit_updated():\n"
                f"    assert policy.LIMIT == {v1}\n\n\n"
                "def test_chain_regression():\n"
                f"    assert hub.{p['fq']}(-2) == 0\n"
                f"    assert store.{p['fp']}('b', 9) is store.DATA\n"
                f"    assert store.LOG['b'] == [9]\n"
            )
        if i == 4:
            return (
                "import hub\nimport policy\n\n\n"
                "def test_trim_none():\n"
                f"    assert hub.{p['ft']}(None) == '-'\n"
                f"    assert hub.{p['ft']}('x') == 'x'\n\n\n"
                "def test_earlier_regression():\n"
                f"    assert hub.{p['fq']}(3) == {3 * mu}\n"
                f"    assert policy.LIMIT == {v1}\n"
            )
        if i == 5:
            return (
                "import hub\nimport report\n\n\n"
                "def test_run():\n"
                f"    assert report.{p['fr']}(3) == 'fee: {3 * mu}'\n\n\n"
                "def test_trim_regression():\n"
                f"    assert hub.{p['ft']}(None) == '-'\n"
            )
        if i == 6:
            return (
                "import report\nimport store\n\n\n"
                "def test_merge():\n"
                f"    assert store.{p['fm']}({{'z': 7}})['z'] == 7\n"
                f"    assert store.{p['fg']}('z') == 7\n\n\n"
                "def test_run_regression():\n"
                f"    assert report.{p['fr']}(3) == 'fee: {3 * mu}'\n"
            )
        if i == 7:
            return (
                "import hub\nimport policy\nimport report\n\n\n"
                "def test_cap():\n"
                f"    assert hub.{p['fcap']}(9999) == {v1}\n"
                f"    assert hub.{p['fcap']}(5) == 5\n\n\n"
                "def test_limit_visible():\n"
                f"    assert policy.LIMIT == {v1}\n"
                f"    assert policy.{p['fc']}(1) is True\n\n\n"
                "def test_report_regression():\n"
                f"    assert report.{p['fr']}(3) == 'fee: {3 * mu}'\n"
            )
        if i == 8:
            return (
                "import report\nimport hub\n\n\n"
                "def test_summary():\n"
                f"    assert report.{p['fs']}([5, 9999]) == ['fee: 5', 'fee: {v1}']\n\n\n"
                "def test_cap_regression():\n"
                f"    assert hub.{p['fcap']}(9999) == {v1}\n"
            )
        if i == 9:
            return (
                "import hub\nimport report\n\n\n"
                "def test_cap_negative():\n"
                f"    assert hub.{p['fcap']}(-3) == 0\n"
                f"    assert hub.{p['fcap']}(9999) == {v1}\n\n\n"
                "def test_summary_regression():\n"
                f"    assert report.{p['fs']}([5, 9999]) == ['fee: 5', 'fee: {v1}']\n"
            )
        # i == 10：策略再次变更 → 动态传播 + 全链回归
        return (
            "import hub\nimport policy\nimport report\nimport store\n\n\n"
            "def test_limit_v2():\n"
            f"    assert policy.LIMIT == {v2}\n"
            f"    assert hub.{p['fcap']}(9999) == {v2}\n"
            f"    assert hub.{p['fcap']}({v2}) == {v2}\n"
            f"    assert hub.{p['fcap']}(-3) == 0\n\n\n"
            "def test_summary_follows_new_limit():\n"
            f"    assert report.{p['fs']}([9999]) == ['fee: {v2}']\n\n\n"
            "def test_full_chain_regression():\n"
            f"    assert hub.{p['fq']}(3) == {3 * mu}\n"
            f"    assert hub.{p['ft']}(None) == '-'\n"
            f"    assert store.{p['fp']}('q', 1) is store.DATA\n"
            f"    assert store.LOG['q'] == [1]\n"
            f"    assert report.{p['fr']}(3) == 'fee: {3 * mu}'\n"
        )

    T(
        id=f"p1_L{p['n']}a",
        family="p1_long_system_evolution",
        type="ten_step_system_evolution",
        difficulty="long",
        focus="10 步系统演进：规格→日志→策略→边界→消费方→封顶→二次策略变更（过期传播）",
        files={
            "hub.py": hub, "store.py": store, "policy.py": pol,
            "report.py": rep, "misc.py": misc,
        },
        steps=[
            {"instruction": (
                f"请修改 hub.py 中的 {p['fq']}(qty)：qty < 0 应返回 0，"
                f"qty ≥ 0 应返回 qty * {mu}（当前实现为 {p['wrong']}）。"
             ), "tests": _t(1),
             "ops": [("replace", "hub.py", s1_old, s1_new)],
             "expect_targets": {"hub.py"}},
            {"instruction": (
                f"store.py 新增 LOG 记录：{p['fp']}(k, v) 在写入 DATA 的同时，"
                f"把 v 追加到 LOG[k]（键不存在先建空列表）；返回值保持 DATA。"
             ), "tests": _t(2),
             "ops": [("replace", "store.py", s2a_old, s2a_new),
                     ("replace", "store.py", s2b_old, s2b_new)],
             "expect_targets": {"store.py"}},
            {"instruction": (
                f"policy.py 中的 LIMIT 应为 {v1}（当前为 {p['v0']}）。"
             ), "tests": _t(3),
             "ops": [("replace", "policy.py", s3_old, s3_new)],
             "expect_targets": {"policy.py"}},
            {"instruction": (
                f"hub.py 中的 {p['ft']}(x)：x 为 None 时应返回 \"-\"（其他输入原样返回）。"
             ), "tests": _t(4),
             "ops": [("replace", "hub.py", s4_old, s4_new)],
             "expect_targets": {"hub.py"}},
            {"instruction": (
                f"report.py 新增 {p['fr']}(qty)：先调用 hub.{p['fq']}(qty)，"
                f"再交给 {p['fl']} 输出（需要补充 import）。"
             ), "tests": _t(5),
             "ops": [("replace", "report.py", s5a_old, s5a_new),
                     ("replace", "report.py", s5b_old, s5b_new)],
             "expect_targets": {"report.py", "hub.py"}},
            {"instruction": (
                f"store.py 新增 {p['fm']}(other)：把字典 other 浅合入 DATA 并返回 DATA。"
             ), "tests": _t(6),
             "ops": [("replace", "store.py", s6_old, s6_new)],
             "expect_targets": {"store.py"}},
            {"instruction": (
                f"hub.py 新增 {p['fcap']}(fee)：fee 超过 policy.py 的 LIMIT 时取 LIMIT，"
                f"否则原样返回（需要 import LIMIT）。"
             ), "tests": _t(7),
             "ops": [("replace", "hub.py", s7a_old, s7a_new),
                     ("replace", "hub.py", s7b_old, s7b_new)],
             "expect_targets": {"hub.py", "policy.py"}},
            {"instruction": (
                f"report.py 新增 {p['fs']}(fees)：对每个 fee 调用 hub.{p['fcap']}，"
                f"并把结果逐个交给 {p['fl']} 返回列表（需要补充 import）。"
             ), "tests": _t(8),
             "ops": [("replace", "report.py", s8a_old, s8a_new),
                     ("replace", "report.py", s8b_old, s8b_new)],
             "expect_targets": {"report.py", "hub.py"}},
            {"instruction": (
                f"hub.py 中的 {p['fcap']}：fee 为负时应返回 0"
                f"（上限截断语义保持不变）。"
             ), "tests": _t(9),
             "ops": [("replace", "hub.py", s9_old, s9_new)],
             "expect_targets": {"hub.py"}},
            {"instruction": (
                f"请修改 policy.py 中的 LIMIT：应从 {v1} 改为 {v2}"
                f"（依赖它的逻辑需保持行为一致）。"
             ), "tests": _t(10),
             "ops": [("replace", "policy.py", s10_old, s10_new)],
             "expect_targets": {"policy.py"}},
        ],
        info_points=[
            {"id": "ip_quote_mult", "type": "implementation",
             "value": f"qty * {mu}", "locator": "instruction:step1 + hub.py",
             "needed_by_steps": [1, 5, 10], "redundant_in_instruction": True},
            {"id": "ip_limit_v1", "type": "critical_data",
             "value": str(v1), "locator": "policy.py:LIMIT after step3 + assistant history",
             "needed_by_steps": [7, 8, 9], "redundant_in_instruction": True},
            {"id": "ip_limit_expiry", "type": "history",
             "value": str(v2), "locator": "instruction:step10 (stale prior value = v1)",
             "needed_by_steps": [10], "redundant_in_instruction": True},
            {"id": "ip_log_contract", "type": "interface",
             "value": "LOG", "locator": "instruction:step2 + store.py",
             "needed_by_steps": [2, 6, 10], "redundant_in_instruction": True},
        ],
    )

# ============================================================ LB 依赖链修造（10 步）
_LB = [
    dict(n="01", leaf="Leaf math", mid="Mid layer", top="Top api",
         cache="Result cache", util="Helper utils",
         flf="shape", lm=2, fmid="adjust", ftop="serve", fcache="warm",
         fsum="total", fagg="serve_all", m2=3, b10=1, wrong="n * 2", tag="lnk-a"),
    dict(n="02", leaf="Leaf units", mid="Mid units", top="Top units",
         cache="Unit cache", util="Unit utils",
         flf="norm", lm=3, fmid="tune", ftop="handle", fcache="prime",
         fsum="sum_all", fagg="handle_all", m2=4, b10=2, wrong="n + 6", tag="lnk-b"),
    dict(n="03", leaf="Leaf tokens", mid="Mid tokens", top="Top tokens",
         cache="Token cache", util="Token utils",
         flf="embed", lm=2, fmid="bias", ftop="push", fcache="prime_t",
         fsum="embed_sum", fagg="push_all", m2=5, b10=1, wrong="n * 5", tag="lnk-c"),
    dict(n="04", leaf="Leaf rows", mid="Mid rows", top="Top rows",
         cache="Row cache", util="Row utils",
         flf="pad", lm=4, fmid="align", ftop="flush", fcache="warm_row",
         fsum="pad_sum", fagg="flush_all", m2=2, b10=3, wrong="n - 4", tag="lnk-d"),
    dict(n="05", leaf="Leaf keys", mid="Mid keys", top="Top keys",
         cache="Key cache", util="Key utils",
         flf="fold", lm=2, fmid="step", ftop="drive", fcache="arm",
         fsum="fold_sum", fagg="drive_all", m2=3, b10=2, wrong="n * 7", tag="lnk-e"),
    dict(n="06", leaf="Leaf cells", mid="Mid cells", top="Top cells",
         cache="Cell cache", util="Cell utils",
         flf="grow", lm=3, fmid="shift", ftop="relay", fcache="load_cell",
         fsum="grow_sum", fagg="relay_all", m2=2, b10=1, wrong="n + 9", tag="lnk-f"),
    dict(n="07", leaf="Leaf stats", mid="Mid stats", top="Top stats",
         cache="Stats cache", util="Stats utils",
         flf="meanish", lm=2, fmid="amp", ftop="serve_s", fcache="prime_s",
         fsum="mean_sum", fagg="serve_many", m2=6, b10=2, wrong="n * 3", tag="lnk-g"),
    dict(n="08", leaf="Leaf frames", mid="Mid frames", top="Top frames",
         cache="Frame cache", util="Frame utils",
         flf="render_n", lm=5, fmid="gate", ftop="dispatch", fcache="prime_f",
         fsum="render_sum", fagg="dispatch_all", m2=2, b10=1, wrong="n + 1", tag="lnk-h"),
]

for p in _LB:
    leaf = (
        f'"""{p["leaf"]}"""\n\n\n'
        f'def {p["flf"]}(n):\n'
        f'    return {p["wrong"]}\n'
    )
    mid = (
        f'"""{p["mid"]}"""\n'
        f'from leaf import {p["flf"]}\n\n\n'
        f'def {p["fmid"]}(n):\n'
        f'    return {p["flf"]}(n) + 1\n'
    )
    top = (
        f'"""{p["top"]}"""\n'
        f'from mid import {p["fmid"]}\n\n\n'
        f'def {p["ftop"]}(n):\n'
        f'    return {p["fmid"]}(n) - 1\n'
    )
    cache = (
        f'"""{p["cache"]}"""\n\n\n'
        f'def {p["fcache"]}(x):\n'
        f'    return "k:" + str(x)\n'
    )
    util = (
        f'"""{p["util"]}"""\n\n\n'
        f'def util_tag():\n'
        f'    return "{p["tag"]}"\n'
    )
    s1_old = f'def {p["flf"]}(n):\n    return {p["wrong"]}\n'
    s1_new = (
        f'def {p["flf"]}(n):\n'
        f'    if n < 0:\n'
        f'    ' + '    return -1\n'
        f'    return n * n\n'
    )
    s2_old = f'def {p["fmid"]}(n):\n    return {p["flf"]}(n) + 1\n'
    s2_new = (
        f'def {p["fmid"]}(n):\n'
        f'    return {p["flf"]}(n) + 1\n\n\n'
        f'def {p["fmid"]}_x2(n):\n'
        f'    return {p["flf"]}(n) * {p["m2"]}\n'
    )
    s3_old = f'def {p["ftop"]}(n):\n    return {p["fmid"]}(n) - 1\n'
    s3_new = f'def {p["ftop"]}(n):\n    return {p["fmid"]}(n)\n'
    s4_old = f'def {p["flf"]}(n):\n    if n < 0:\n        return -1\n    return n * n\n'
    s4_new = (
        f'def {p["flf"]}(n):\n'
        f'    if n < 0:\n'
        f'        return -1\n'
        f'    return n * n\n\n\n'
        f'def {p["fsum"]}(nums):\n'
        f'    if not nums:\n'
        f'        return -1\n'
        f'    return sum({p["flf"]}(x) for x in nums)\n'
    )
    s5a_old = f'def {p["fmid"]}(n):\n    return {p["flf"]}(n) + 1\n'
    s5a_new = f'def {p["fmid"]}(n, boost):\n    return {p["flf"]}(n) + 1 + boost\n'
    s5b_old = f'def {p["ftop"]}(n):\n    return {p["fmid"]}(n)\n'
    s5b_new = f'def {p["ftop"]}(n):\n    return {p["fmid"]}(n, 0)\n'
    s6a_old = f'"""{p["cache"]}"""\n\n'
    s6a_new = f'"""{p["cache"]}"""\nfrom top import {p["ftop"]}\n\n'
    s6b_old = f'def {p["fcache"]}(x):\n    return "k:" + str(x)\n'
    s6b_new = (
        f'def {p["fcache"]}(x):\n'
        f'    return "k:" + str(x)\n\n\n'
        f'def {p["fcache"]}_serve(n):\n'
        f'    return {p["ftop"]}(n) + {abs(p["b10"] - 1) + 1}\n'
    )
    s7_old = f'def {p["fmid"]}(n, boost):\n    return {p["flf"]}(n) + 1 + boost\n'
    s7_new = (
        f'def {p["fmid"]}(n, boost):\n'
        f'    if boost < 0:\n'
        f'        raise ValueError("boost must be >= 0")\n'
        f'    return {p["flf"]}(n) + 1 + boost\n'
    )
    s8_old = f'def {p["ftop"]}(n):\n    return {p["fmid"]}(n, 0)\n'
    s8_new = (
        f'def {p["ftop"]}(n):\n'
        f'    return {p["fmid"]}(n, 0)\n\n\n'
        f'def {p["fagg"]}(ns):\n'
        f'    return [{p["ftop"]}(x) for x in ns]\n'
    )
    s9_old = (
        f'def {p["fsum"]}(nums):\n'
        f'    if not nums:\n'
        f'        return -1\n'
        f'    return sum({p["flf"]}(x) for x in nums)\n'
    )
    s9_new = (
        f'def {p["fsum"]}(nums):\n'
        f'    if not nums:\n'
        f'        return -1\n'
        f'    if any({p["flf"]}(x) == -1 for x in nums):\n'
        f'        return -1\n'
        f'    return sum({p["flf"]}(x) for x in nums)\n'
    )
    s10_old = f'def {p["ftop"]}(n):\n    return {p["fmid"]}(n, 0)\n'
    s10_new = (
        f'def {p["ftop"]}(n):\n'
        f'    return {p["fmid"]}(n, {p["b10"]})\n'
    )
    b10, m2 = p["b10"], p["m2"]

    def _t(i, p=p, b10=b10, m2=m2):
        # 常用断言（初值：shape(3)=9; adjust(3)=10; serve(3)=9）
        if i == 1:
            return (
                f"from leaf import {p['flf']}\n\n\n"
                "def test_shape():\n"
                f"    assert {p['flf']}(-2) == -1\n"
                f"    assert {p['flf']}(3) == 9\n"
                f"    assert {p['flf']}(0) == 0\n"
            )
        if i == 2:
            return (
                f"from leaf import {p['flf']}\n"
                f"from mid import {p['fmid']}, {p['fmid']}_x2\n\n\n"
                "def test_mid_x2():\n"
                f"    assert {p['fmid']}_x2(3) == {9 * m2}\n"
                f"    assert {p['fmid']}_x2(-2) == {-m2}\n\n\n"
                "def test_mid_base():\n"
                f"    assert {p['fmid']}(3) == 10\n"
            )
        if i == 3:
            return (
                f"from mid import {p['fmid']}\n"
                f"from top import {p['ftop']}\n\n\n"
                "def test_top_fixed():\n"
                f"    assert {p['ftop']}(3) == 10\n\n\n"
                "def test_mid_regression():\n"
                f"    assert {p['fmid']}(3) == 10\n"
                f"    assert {p['fmid']}(-2) == 0\n"
            )
        if i == 4:
            return (
                f"from leaf import {p['flf']}, {p['fsum']}\n"
                f"from top import {p['ftop']}\n\n\n"
                "def test_sum_empty():\n"
                f"    assert {p['fsum']}([]) == -1\n"
                "def test_sum_values():\n"
                f"    assert {p['fsum']}([2, 3]) == 13\n\n\n"
                "def test_top_regression():\n"
                f"    assert {p['ftop']}(3) == 10\n"
            )
        if i == 5:
            return (
                f"from mid import {p['fmid']}\n"
                f"from top import {p['ftop']}\n"
                f"from leaf import {p['fsum']}\n\n\n"
                "def test_synced_signature():\n"
                f"    assert {p['fmid']}(3, 2) == 12\n"
                f"    assert {p['ftop']}(3) == 10\n\n\n"
                "def test_leaf_regression():\n"
                f"    assert {p['fsum']}([2, 3]) == 13\n"
            )
        if i == 6:
            bias = abs(b10 - 1) + 1
            return (
                f"from top import {p['ftop']}\n"
                f"from cache import {p['fcache']}_serve\n"
                f"from mid import {p['fmid']}\n\n\n"
                "def test_cache_consumer():\n"
                f"    assert {p['fcache']}_serve(3) == {10 + bias}\n\n\n"
                "def test_mid_regression():\n"
                f"    assert {p['fmid']}(3, 0) == 10\n"
            )
        if i == 7:
            return (
                f"from mid import {p['fmid']}\n"
                f"from top import {p['ftop']}\n"
                "import pytest\n\n\n"
                "def test_boost_validation():\n"
                "    with pytest.raises(ValueError):\n"
                f"        {p['fmid']}(3, -1)\n\n\n"
                "def test_chain_regression():\n"
                f"    assert {p['fmid']}(3, 2) == 12\n"
                f"    assert {p['ftop']}(3) == 10\n"
            )
        if i == 9:
            return (
                f"from leaf import {p['fsum']}, {p['flf']}\n"
                f"from top import {p['ftop']}\n\n\n"
                "def test_sum_any_negative():\n"
                f"    assert {p['fsum']}([2, -1]) == -1\n"
                f"    assert {p['fsum']}([2, 3]) == 13\n"
                f"    assert {p['fsum']}([]) == -1\n\n\n"
                "def test_top_regression():\n"
                f"    assert {p['ftop']}(3) == 10\n"
            )
        # i == 10
        return (
            f"from mid import {p['fmid']}\n"
            f"from top import {p['ftop']}, {p['fagg']}\n"
            f"from leaf import {p['fsum']}\n\n\n"
            "def test_top_boost_applied():\n"
            f"    assert {p['ftop']}(3) == {10 + b10}\n\n\n"
            "def test_agg_follows_top():\n"
            f"    assert {p['fagg']}([3]) == [{10 + b10}]\n\n\n"
            "def test_full_chain_regression():\n"
            f"    assert {p['fmid']}(3, 2) == 12\n"
            f"    assert {p['fsum']}([2, 3]) == 13\n"
            f"    assert {p['fsum']}([2, -1]) == -1\n"
        )

    # i==8 分支修正（上面对 8 的实现有残片，用干净版本覆盖）
    def _t8(p=p, b10=b10):
        bias = abs(b10 - 1) + 1
        return (
            f"from top import {p['ftop']}, {p['fagg']}\n"
            f"from cache import {p['fcache']}_serve\n\n\n"
            "def test_agg():\n"
            f"    assert {p['fagg']}([3, 4]) == [10, 17]\n\n\n"
            "def test_cache_regression():\n"
            f"    assert {p['fcache']}_serve(3) == {10 + bias}\n"
        )

    T(
        id=f"p1_L{p['n']}b",
        family="p1_long_dependency_chain",
        type="ten_step_dependency_chain",
        difficulty="long",
        focus="10 步依赖链：leaf→mid→top 修造 + 签名同步 + 校验 + 回溯修订",
        files={
            "leaf.py": leaf, "mid.py": mid, "top.py": top,
            "cache.py": cache, "util.py": util,
        },
        steps=[
            {"instruction": (
                f"请修改 leaf.py 中的 {p['flf']}(n)：n < 0 应返回 -1，"
                f"n ≥ 0 应返回 n * n（当前实现为 {p['wrong']}）。"
             ), "tests": _t(1),
             "ops": [("replace", "leaf.py", s1_old, s1_new)],
             "expect_targets": {"leaf.py"}},
            {"instruction": (
                f"mid.py 新增 {p['fmid']}_x2(n)：应返回 n * n * {m2}。"
                f"平方口径见 leaf.py 的 {p['flf']}，该文件无需改动。"
             ), "tests": _t(2),
             "ops": [("replace", "mid.py", s2_old, s2_new)],
             "expect_targets": {"mid.py"}},
            {"instruction": (
                f"top.py 中的 {p['ftop']}：应直接返回中间层结果"
                f"（当前实现多减了 1）。中间层入口为 mid.py 的 {p['fmid']}。"
             ), "tests": _t(3),
             "ops": [("replace", "top.py", s3_old, s3_new)],
             "expect_targets": {"top.py"}},
            {"instruction": (
                f"leaf.py 新增 {p['fsum']}(nums)：空列表返回 -1，"
                f"否则返回各元素经 {p['flf']} 变换后的和。"
             ), "tests": _t(4),
             "ops": [("replace", "leaf.py", s4_old, s4_new)],
             "expect_targets": {"leaf.py"}},
            {"instruction": (
                f"mid.py 中的 {p['fmid']} 改签名为 (n, boost) 必填：返回值在原有基础上再加 boost。"
                f"同步更新 top.py 的调用方（传 0 保持原行为）。"
             ), "tests": _t(5),
             "ops": [("replace", "mid.py", s5a_old, s5a_new),
                     ("replace", "top.py", s5b_old, s5b_new)],
             "expect_targets": {"mid.py", "top.py"}},
            {"instruction": (
                f"cache.py 新增 {p['fcache']}_serve(n)：调用 top.{p['ftop']}(n)"
                f" 并返回结果加 {abs(p['b10'] - 1) + 1}（需要补充 import）。"
             ), "tests": _t(6),
             "ops": [("replace", "cache.py", s6a_old, s6a_new),
                     ("replace", "cache.py", s6b_old, s6b_new)],
             "expect_targets": {"cache.py", "top.py"}},
            {"instruction": (
                f"请修改 mid.py 中的 {p['fmid']}：boost < 0 时应抛 ValueError"
                f"（boost ≥ 0 行为不变）。"
             ), "tests": _t(7),
             "ops": [("replace", "mid.py", s7_old, s7_new)],
             "expect_targets": {"mid.py"}},
            {"instruction": (
                f"top.py 新增 {p['fagg']}(ns)：对每个 n 调用 {p['ftop']} 并返回结果列表。"
             ), "tests": _t8(),
             "ops": [("replace", "top.py", s8_old, s8_new)],
             "expect_targets": {"top.py"}},
            {"instruction": (
                f"leaf.py 中的 {p['fsum']}：nums 中只要有一个元素经 {p['flf']}"
                f" 变换为 -1，整体应返回 -1（其余规则不变）。"
             ), "tests": _t(9),
             "ops": [("replace", "leaf.py", s9_old, s9_new)],
             "expect_targets": {"leaf.py"}},
            {"instruction": (
                f"top.py 中的 {p['ftop']}：应改为返回 {p['fmid']}(n, {b10})"
                f"（当前固定传 0；下游行为需同步一致）。"
             ), "tests": _t(10),
             "ops": [("replace", "top.py", s10_old, s10_new)],
             "expect_targets": {"top.py", "mid.py"}},
        ],
        info_points=[
            {"id": "ip_square_rule", "type": "implementation",
             "value": "return n * n", "locator": "instruction:step1 + leaf.py",
             "needed_by_steps": [1, 2, 4, 9], "redundant_in_instruction": True},
            {"id": "ip_boost_signature", "type": "history",
             "value": f"{p['fmid']}(n, boost)",
             "locator": "mid.py after step5 + assistant history",
             "needed_by_steps": [7, 10], "redundant_in_instruction": True},
            {"id": "ip_top_boost_value", "type": "critical_data",
             "value": str(b10), "locator": "instruction:step10",
             "needed_by_steps": [10], "redundant_in_instruction": True},
            {"id": "ip_chain_top_value", "type": "implementation",
             "value": f"{p['fmid']}(n)", "locator": "top.py after step3",
             "needed_by_steps": [5, 6], "redundant_in_instruction": True},
        ],
    )
