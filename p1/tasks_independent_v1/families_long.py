"""独立任务集 Long 族（Part2 independent-v1）：8 archetype × 2 变体 = 16 题，每题 10 步。

骨架：调度 / 记账 / 库存 / 命令日志 / 图 / 消息协议 / 仓储 / 插件。
同骨架两变体在实体、数据结构与控制流上实质不同（非纯换名）。
"""

from registry import T

# ============================================================ LF1 ind_long_scheduler
# 变体 a：优先级任务队列（列表三元组 + 入队序号 tie-break）

_jobs_a = (
    '"""Job queue."""\n\n\n'
    "QUEUE = []\n\n\n"
    "def push(job, prio):\n"
    "    QUEUE.append((job, prio))\n\n\n"
    "def pop():\n"
    "    if not QUEUE:\n"
    "        return None\n"
    "    return QUEUE.pop(0)[0]\n"
)
_pol_a = (
    '"""Scheduling policy."""\n\n\n'
    "MIN_PRIO = 0\n"
)
_rep_a = (
    '"""Queue report."""\n\n\n'
    "def size_line(n):\n"
    '    return f"size={n}"\n'
)
_j1_old = (
    "QUEUE = []\n\n\n"
    "def push(job, prio):\n"
    "    QUEUE.append((job, prio))\n\n\n"
    "def pop():\n"
    "    if not QUEUE:\n"
    "        return None\n"
    "    return QUEUE.pop(0)[0]"
)
_j1_new = (
    "QUEUE = []\n"
    "SEQ = 0\n\n\n"
    "def push(job, prio):\n"
    "    global SEQ\n"
    "    SEQ += 1\n"
    "    QUEUE.append((job, prio, SEQ))\n\n\n"
    "def pop():\n"
    "    if not QUEUE:\n"
    "        return None\n"
    "    QUEUE.sort(key=lambda t: (-t[1], t[2]))\n"
    "    return QUEUE.pop(0)[0]"
)
_j2a_old = '"""Job queue."""'
_j2a_new = '"""Job queue."""\nfrom policy import MIN_PRIO'
_j2b_old = "def push(job, prio):\n    global SEQ\n"
_j2b_new = (
    "def push(job, prio):\n"
    '    if prio < MIN_PRIO:\n'
    '        raise ValueError("prio")\n'
    "    global SEQ\n"
)
_j3_old = (
    "    QUEUE.sort(key=lambda t: (-t[1], t[2]))\n"
    "    return QUEUE.pop(0)[0]"
)
_j3_new = _j3_old + (
    "\n\n\ndef bump(job, prio):\n"
    "    for i, t in enumerate(QUEUE):\n"
    "        if t[0] == job:\n"
    "            QUEUE[i] = (job, prio, t[2])\n"
    "            return True\n"
    "    return False"
)
_j4a_old = '"""Queue report."""'
_j4a_new = '"""Queue report."""\nfrom jobsched import QUEUE'
_j4b_old = 'def size_line(n):\n    return f"size={n}"'
_j4b_new = _j4b_old + (
    "\n\n\ndef preview():\n"
    "    if not QUEUE:\n"
    "        return None\n"
    "    ordered = sorted(QUEUE, key=lambda t: (-t[1], t[2]))\n"
    "    return ordered[0][0]"
)
_j5_old = (
    "        if t[0] == job:\n"
    "            QUEUE[i] = (job, prio, t[2])\n"
    "            return True\n"
    "    return False"
)
_j5_new = _j5_old + (
    "\n\n\ndef take(n):\n"
    "    out = []\n"
    "    for _ in range(n):\n"
    "        job = pop()\n"
    "        if job is None:\n"
    "            break\n"
    "        out.append(job)\n"
    "    return out"
)
_j6a_old = "MIN_PRIO = 0\n"
_j6a_new = "MIN_PRIO = 0\nCAP = 3\n"
_j6b_old = "from policy import MIN_PRIO"
_j6b_new = "from policy import MIN_PRIO, CAP"
_j6c_old = (
    "    if prio < MIN_PRIO:\n"
    '        raise ValueError("prio")\n'
    "    global SEQ\n"
)
_j6c_new = (
    "    if prio < MIN_PRIO:\n"
    '        raise ValueError("prio")\n'
    "    if len(QUEUE) >= CAP:\n"
    '        raise ValueError("full")\n'
    "    global SEQ\n"
)
_j7_old = (
    "def preview():\n"
    "    if not QUEUE:\n"
    "        return None\n"
    "    ordered = sorted(QUEUE, key=lambda t: (-t[1], t[2]))\n"
    "    return ordered[0][0]"
)
_j7_new = _j7_old + (
    "\n\n\ndef summary():\n"
    '    ordered = sorted(QUEUE, key=lambda t: (-t[1], t[2]))\n'
    '    return [f"{t[0]}@{t[1]}" for t in ordered]'
)
_j8a_old = (
    "    QUEUE.sort(key=lambda t: (-t[1], t[2]))\n"
    "    return QUEUE.pop(0)[0]"
)
_j8a_new = (
    "    QUEUE.sort(key=lambda t: (-t[1], t[0]))\n"
    "    return QUEUE.pop(0)[0]"
)
_j8b_old = (
    "    ordered = sorted(QUEUE, key=lambda t: (-t[1], t[2]))\n"
    "    return ordered[0][0]"
)
_j8b_new = (
    "    ordered = sorted(QUEUE, key=lambda t: (-t[1], t[0]))\n"
    "    return ordered[0][0]"
)
_j8c_old = (
    '    ordered = sorted(QUEUE, key=lambda t: (-t[1], t[2]))\n'
    '    return [f"{t[0]}@{t[1]}" for t in ordered]'
)
_j8c_new = (
    '    ordered = sorted(QUEUE, key=lambda t: (-t[1], t[0]))\n'
    '    return [f"{t[0]}@{t[1]}" for t in ordered]'
)
_j9_old = (
    "def bump(job, prio):\n"
    "    for i, t in enumerate(QUEUE):\n"
    "        if t[0] == job:\n"
    "            QUEUE[i] = (job, prio, t[2])\n"
    "            return True\n"
    "    return False"
)
_j9_new = (
    "def bump(job, prio):\n"
    "    for i, t in enumerate(QUEUE):\n"
    "        if t[0] == job:\n"
    "            QUEUE[i] = (job, prio, t[2])\n"
    "            return True\n"
    "    raise KeyError(job)"
)
T(
    id="ind_L01a",
    family="ind_long_scheduler",
    type="priority_queue_evolution",
    difficulty="long",
    focus="10 步优先级队列演进：排序出队→边界拒绝→改约→批量→满仓→tie-break 改约→策略二次变更",
    files={"jobsched.py": _jobs_a, "policy.py": _pol_a, "report.py": _rep_a},
    steps=[
        {
            "instruction": (
                "请修改 jobsched.py 中的 push 与 pop：出队时优先级数值大的先出，"
                "优先级相同按入队先后（先入队先出）；空队列出队返回 None。"
            ),
            "tests": (
                "import jobsched\n\n\n"
                "def test_priority_order():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    jobsched.push("c", 3)\n'
                '    assert jobsched.pop() == "b"\n'
                '    assert jobsched.pop() == "c"\n'
                '    assert jobsched.pop() == "a"\n\n\n'
                "def test_fifo_within_priority():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("z", 4)\n'
                '    jobsched.push("y", 4)\n'
                '    assert jobsched.pop() == "z"\n'
                '    assert jobsched.pop() == "y"\n\n\n'
                "def test_empty():\n"
                "    jobsched.QUEUE.clear()\n"
                "    assert jobsched.pop() is None\n"
            ),
            "ops": [("replace", "jobsched.py", _j1_old, _j1_new)],
            "expect_targets": {"jobsched.py"},
        },
        {
            "instruction": (
                "请修改 jobsched.py 中的 push：prio 小于 policy.py 的 MIN_PRIO 时抛 ValueError；"
                "合法入队仍按原顺序记录。"
            ),
            "tests": (
                "import pytest\n"
                "import jobsched\n\n\n"
                "def test_reject_below_min():\n"
                "    jobsched.QUEUE.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        jobsched.push("x", -1)\n\n\n'
                "def test_accept_min():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 0)\n'
                '    assert jobsched.pop() == "a"\n\n\n'
                "def test_order_regression():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    assert jobsched.pop() == "b"\n'
                '    assert jobsched.pop() == "a"\n'
            ),
            "ops": [
                ("replace", "jobsched.py", _j2a_old, _j2a_new),
                ("replace", "jobsched.py", _j2b_old, _j2b_new),
            ],
            "expect_targets": {"jobsched.py", "policy.py"},
        },
        {
            "instruction": (
                "jobsched.py 新增 bump(job, prio)：把队列中同名任务的优先级改为 prio "
                "并保留其入队序号，返回是否找到该任务（找不到返回 False）。"
            ),
            "tests": (
                "import jobsched\n\n\n"
                "def test_bump_found():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    assert jobsched.bump("a", 9) is True\n'
                '    assert jobsched.pop() == "a"\n'
                '    assert jobsched.pop() == "b"\n\n\n'
                "def test_bump_missing():\n"
                "    jobsched.QUEUE.clear()\n"
                '    assert jobsched.bump("ghost", 3) is False\n\n\n'
                "def test_reject_regression():\n"
                "    import pytest\n"
                "    jobsched.QUEUE.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        jobsched.push("x", -1)\n'
            ),
            "ops": [("replace", "jobsched.py", _j3_old, _j3_new)],
            "expect_targets": {"jobsched.py"},
        },
        {
            "instruction": (
                "report.py 新增 preview()：返回队列中下一将出队的任务（不弹出队列），"
                "空队列返回 None（需要补充 import）。"
            ),
            "tests": (
                "import jobsched\n"
                "import report\n\n\n"
                "def test_preview():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    assert report.preview() == "b"\n'
                "    assert len(jobsched.QUEUE) == 2\n\n\n"
                "def test_preview_empty():\n"
                "    jobsched.QUEUE.clear()\n"
                "    assert report.preview() is None\n\n\n"
                "def test_bump_regression():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    assert jobsched.bump("a", 9) is True\n'
                '    assert jobsched.pop() == "a"\n'
            ),
            "ops": [
                ("replace", "report.py", _j4a_old, _j4a_new),
                ("replace", "report.py", _j4b_old, _j4b_new),
            ],
            "expect_targets": {"report.py"},
        },
        {
            "instruction": (
                "jobsched.py 新增 take(n)：按当前出队顺序连续出队至多 n 个任务并返回列表；"
                "不足 n 个时返回已出队部分（空队列返回空列表）。"
            ),
            "tests": (
                "import jobsched\n"
                "import report\n\n\n"
                "def test_take_batch():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    jobsched.push("c", 3)\n'
                '    assert jobsched.take(2) == ["b", "c"]\n'
                "    assert len(jobsched.QUEUE) == 1\n\n\n"
                "def test_take_more_than_size():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 2)\n'
                '    assert jobsched.take(5) == ["a"]\n'
                "    assert jobsched.QUEUE == []\n\n\n"
                "def test_preview_regression():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    assert report.preview() == "b"\n'
            ),
            "ops": [("replace", "jobsched.py", _j5_old, _j5_new)],
            "expect_targets": {"jobsched.py"},
        },
        {
            "instruction": (
                "policy.py 新增 CAP = 3；请修改 jobsched.py 中的 push："
                "队列长度已达 CAP 时抛 ValueError（需要同步 import）。"
            ),
            "tests": (
                "import pytest\n"
                "import jobsched\n"
                "import policy\n\n\n"
                "def test_cap_constant():\n"
                "    assert policy.CAP == 3\n\n\n"
                "def test_full_queue():\n"
                "    jobsched.QUEUE.clear()\n"
                '    for i in range(3):\n'
                '        jobsched.push(f"j{i}", 2)\n'
                "    with pytest.raises(ValueError):\n"
                '        jobsched.push("extra", 2)\n\n\n'
                "def test_take_regression():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    assert jobsched.take(2) == ["b", "a"]\n'
            ),
            "ops": [
                ("replace", "policy.py", _j6a_old, _j6a_new),
                ("replace", "jobsched.py", _j6b_old, _j6b_new),
                ("replace", "jobsched.py", _j6c_old, _j6c_new),
            ],
            "expect_targets": {"policy.py", "jobsched.py"},
        },
        {
            "instruction": (
                "report.py 新增 summary()：按出队顺序把每个任务格式化为 '任务名@优先级' "
                "并返回列表（空队列返回空列表）。"
            ),
            "tests": (
                "import jobsched\n"
                "import report\n\n\n"
                "def test_summary():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    assert report.summary() == ["b@5", "a@1"]\n\n\n'
                "def test_summary_empty():\n"
                "    jobsched.QUEUE.clear()\n"
                "    assert report.summary() == []\n\n\n"
                "def test_take_regression():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("x", 2)\n'
                '    jobsched.push("y", 4)\n'
                '    assert jobsched.take(1) == ["y"]\n'
            ),
            "ops": [("replace", "report.py", _j7_old, _j7_new)],
            "expect_targets": {"report.py"},
        },
        {
            "instruction": (
                "请修改 jobsched.py 的 pop 与 report.py 的 preview、summary："
                "同优先级任务改为按任务名字典序先后派发（取代入队先后规则）。"
            ),
            "tests": (
                "import jobsched\n"
                "import report\n\n\n"
                "def test_name_tiebreak():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("zeta", 5)\n'
                '    jobsched.push("alpha", 5)\n'
                '    assert jobsched.pop() == "alpha"\n'
                '    assert jobsched.pop() == "zeta"\n\n\n'
                "def test_preview_follows_rule():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("zeta", 5)\n'
                '    jobsched.push("alpha", 5)\n'
                '    assert report.preview() == "alpha"\n\n\n'
                "def test_summary_follows_rule():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("zeta", 5)\n'
                '    jobsched.push("alpha", 5)\n'
                '    assert report.summary() == ["alpha@5", "zeta@5"]\n'
            ),
            "ops": [
                ("replace", "jobsched.py", _j8a_old, _j8a_new),
                ("replace", "report.py", _j8b_old, _j8b_new),
                ("replace", "report.py", _j8c_old, _j8c_new),
            ],
            "expect_targets": {"jobsched.py", "report.py"},
        },
        {
            "instruction": (
                "请修改 jobsched.py 中的 bump：任务不在队列时应抛 KeyError"
                "（找到任务时仍返回 True）。"
            ),
            "tests": (
                "import pytest\n"
                "import jobsched\n\n\n"
                "def test_bump_missing_raises():\n"
                "    jobsched.QUEUE.clear()\n"
                "    with pytest.raises(KeyError):\n"
                '        jobsched.bump("ghost", 3)\n\n\n'
                "def test_bump_found_regression():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("a", 1)\n'
                '    jobsched.push("b", 5)\n'
                '    assert jobsched.bump("a", 9) is True\n'
                '    assert jobsched.pop() == "a"\n\n\n'
                "def test_name_tiebreak_regression():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("zeta", 5)\n'
                '    jobsched.push("alpha", 5)\n'
                '    assert jobsched.pop() == "alpha"\n'
            ),
            "ops": [("replace", "jobsched.py", _j9_old, _j9_new)],
            "expect_targets": {"jobsched.py"},
        },
        {
            "instruction": (
                "请修改 policy.py 中的 MIN_PRIO：应从 0 改为 2，"
                "使 prio 小于 2 的入队一律被拒绝。"
            ),
            "tests": (
                "import pytest\n"
                "import jobsched\n"
                "import policy\n"
                "import report\n\n\n"
                "def test_min_prio_updated():\n"
                "    assert policy.MIN_PRIO == 2\n"
                "    jobsched.QUEUE.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        jobsched.push("x", 1)\n'
                '    jobsched.push("y", 2)\n'
                '    assert jobsched.pop() == "y"\n\n\n'
                "def test_full_chain():\n"
                "    jobsched.QUEUE.clear()\n"
                '    jobsched.push("beta", 4)\n'
                '    jobsched.push("alpha", 4)\n'
                '    assert report.preview() == "alpha"\n'
                '    assert report.summary() == ["alpha@4", "beta@4"]\n'
                '    assert jobsched.bump("beta", 9) is True\n'
                '    assert jobsched.take(2) == ["beta", "alpha"]\n'
                "    assert policy.CAP == 3\n"
            ),
            "ops": [("replace", "policy.py", "MIN_PRIO = 0\n", "MIN_PRIO = 2\n")],
            "expect_targets": {"policy.py"},
        },
    ],
    info_points=[
        {"id": "ip_order_rule", "type": "implementation",
         "value": "出队按 (-prio, tiebreak) 排序",
         "locator": "instruction:step1 + jobsched.py",
         "needed_by_steps": [1, 3, 5, 7, 8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_min_prio_chain", "type": "critical_data",
         "value": "MIN_PRIO：0（step2 起）→ 2（step10）",
         "locator": "instruction:step2 + instruction:step10 + policy.py",
         "needed_by_steps": [2, 10],
         "redundant_in_instruction": True},
        {"id": "ip_bump_contract", "type": "interface",
         "value": "bump 返回 bool（step9 改为抛 KeyError）",
         "locator": "instruction:step3 + instruction:step9",
         "needed_by_steps": [3, 9],
         "redundant_in_instruction": True},
        {"id": "ip_queue_tuple", "type": "history",
         "value": "QUEUE 元素为 (job, prio, seq) 三元组",
         "locator": "jobsched.py after step1 + assistant history",
         "needed_by_steps": [3, 5, 7, 8],
         "redundant_in_instruction": False},
        {"id": "ip_cap_value", "type": "critical_data",
         "value": "CAP = 3",
         "locator": "instruction:step6 + policy.py",
         "needed_by_steps": [6, 10],
         "redundant_in_instruction": True},
    ],
)

# 变体 b：分级派发台（字典分桶 + 按 level 降序取号）

_desk_b = (
    '"""Dispatch desk."""\n\n\n'
    "BUCKETS = {}\n\n\n"
    "def admit(job, level):\n"
    "    BUCKETS.setdefault(level, []).append(job)\n\n\n"
    "def next_job():\n"
    "    for lvl in sorted(BUCKETS):\n"
    "        if BUCKETS[lvl]:\n"
    "            return BUCKETS[lvl].pop(0)\n"
    "    return None\n"
)
_rules_b = (
    '"""Desk rules."""\n\n\n'
    "DEFAULT_LEVEL = 1\n"
    "MIN_LEVEL = 0\n"
    "MAX_LEVEL = 9\n"
)
_cons_b = (
    '"""Desk console."""\n\n\n'
    "def show(job):\n"
    '    return f"job={job}"\n'
)
_d1_old = "    for lvl in sorted(BUCKETS):"
_d1_new = "    for lvl in sorted(BUCKETS, reverse=True):"
_d2a_old = '"""Dispatch desk."""'
_d2a_new = '"""Dispatch desk."""\nfrom rules import MIN_LEVEL, MAX_LEVEL'
_d2b_old = (
    "def admit(job, level):\n"
    "    BUCKETS.setdefault(level, []).append(job)"
)
_d2b_new = (
    "def admit(job, level):\n"
    "    if level < MIN_LEVEL or level > MAX_LEVEL:\n"
    '        raise ValueError("level")\n'
    "    BUCKETS.setdefault(level, []).append(job)"
)
_d3_old = (
    "def next_job():\n"
    "    for lvl in sorted(BUCKETS, reverse=True):\n"
    "        if BUCKETS[lvl]:\n"
    "            return BUCKETS[lvl].pop(0)\n"
    "    return None"
)
_d3_new = _d3_old + "\n\n\ndef count(level):\n    return len(BUCKETS.get(level, []))"
_d4a_old = '"""Desk console."""'
_d4a_new = '"""Desk console."""\nfrom desk import BUCKETS'
_d4b_old = 'def show(job):\n    return f"job={job}"'
_d4b_new = _d4b_old + (
    "\n\n\ndef board():\n"
    "    return {lvl: len(jobs) for lvl, jobs in BUCKETS.items()}"
)
_d5_old = "def count(level):\n    return len(BUCKETS.get(level, []))"
_d5_new = _d5_old + (
    "\n\n\ndef drain(level, n):\n"
    "    out = []\n"
    "    bucket = BUCKETS.get(level, [])\n"
    "    limit = min(n, len(bucket))\n"
    "    for _ in range(limit):\n"
    "        out.append(bucket.pop(0))\n"
    "    return out"
)
_d6a_old = "from rules import MIN_LEVEL, MAX_LEVEL"
_d6a_new = "from rules import DEFAULT_LEVEL, MIN_LEVEL, MAX_LEVEL"
_d6b_old = (
    "def admit(job, level):\n"
    "    if level < MIN_LEVEL or level > MAX_LEVEL:\n"
    '        raise ValueError("level")\n'
    "    BUCKETS.setdefault(level, []).append(job)"
)
_d6b_new = (
    "def admit(job, level=None):\n"
    "    if level is None:\n"
    "        level = DEFAULT_LEVEL\n"
    "    if level < MIN_LEVEL or level > MAX_LEVEL:\n"
    '        raise ValueError("level")\n'
    "    BUCKETS.setdefault(level, []).append(job)"
)
_d7_old = (
    "    limit = min(n, len(bucket))\n"
    "    for _ in range(limit):\n"
    "        out.append(bucket.pop(0))\n"
    "    return out"
)
_d7_new = _d7_old + (
    "\n\n\ndef levels():\n"
    "    return sorted((lvl for lvl, jobs in BUCKETS.items() if jobs), reverse=True)"
)
_d8_old = (
    "    if level < MIN_LEVEL or level > MAX_LEVEL:\n"
    '        raise ValueError("level")'
)
_d8_new = (
    "    if level < MIN_LEVEL:\n"
    "        level = MIN_LEVEL\n"
    "    if level > MAX_LEVEL:\n"
    "        level = MAX_LEVEL"
)
_d9_old = (
    "def next_job():\n"
    "    for lvl in sorted(BUCKETS, reverse=True):\n"
    "        if BUCKETS[lvl]:\n"
    "            return BUCKETS[lvl].pop(0)\n"
    "    return None"
)
_d9_new = (
    "def next_job():\n"
    "    for lvl in sorted(BUCKETS, reverse=True):\n"
    "        if BUCKETS[lvl]:\n"
    "            job = BUCKETS[lvl].pop(0)\n"
    "            if not BUCKETS[lvl]:\n"
    "                del BUCKETS[lvl]\n"
    "            return job\n"
    "    return None"
)
T(
    id="ind_L01b",
    family="ind_long_scheduler",
    type="priority_queue_evolution",
    difficulty="long",
    focus="10 步分桶派发台演进：降序取号→越界拒绝→统计→默认档→钳制改约→空桶回收→策略二次变更",
    files={"desk.py": _desk_b, "rules.py": _rules_b, "console.py": _cons_b},
    steps=[
        {
            "instruction": (
                "请修改 desk.py 中的 next_job：level 数值大的任务先派发"
                "（同一 level 内保持先入先出）；没有任务时返回 None。"
            ),
            "tests": (
                "import desk\n\n\n"
                "def test_high_first():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("low", 1)\n'
                '    desk.admit("high", 7)\n'
                '    desk.admit("mid", 4)\n'
                '    assert desk.next_job() == "high"\n'
                '    assert desk.next_job() == "mid"\n'
                '    assert desk.next_job() == "low"\n\n\n'
                "def test_fifo_within_level():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("first", 3)\n'
                '    desk.admit("second", 3)\n'
                '    assert desk.next_job() == "first"\n'
                '    assert desk.next_job() == "second"\n\n\n'
                "def test_empty():\n"
                "    desk.BUCKETS.clear()\n"
                "    assert desk.next_job() is None\n"
            ),
            "ops": [("replace", "desk.py", _d1_old, _d1_new)],
            "expect_targets": {"desk.py"},
        },
        {
            "instruction": (
                "请修改 desk.py 中的 admit：level 超出 rules.py 的 MIN_LEVEL 与 MAX_LEVEL "
                "范围时抛 ValueError（需要补充 import）。"
            ),
            "tests": (
                "import pytest\n"
                "import desk\n\n\n"
                "def test_out_of_range():\n"
                "    desk.BUCKETS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        desk.admit("x", 10)\n'
                "    with pytest.raises(ValueError):\n"
                '        desk.admit("x", -1)\n\n\n'
                "def test_in_range():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("ok", 5)\n'
                '    assert desk.next_job() == "ok"\n\n\n'
                "def test_high_first_regression():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("low", 1)\n'
                '    desk.admit("high", 7)\n'
                '    assert desk.next_job() == "high"\n'
            ),
            "ops": [
                ("replace", "desk.py", _d2a_old, _d2a_new),
                ("replace", "desk.py", _d2b_old, _d2b_new),
            ],
            "expect_targets": {"desk.py", "rules.py"},
        },
        {
            "instruction": (
                "desk.py 新增 count(level)：返回该 level 当前排队任务数"
                "（没有该 level 时返回 0）。"
            ),
            "tests": (
                "import desk\n\n\n"
                "def test_count():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("a", 2)\n'
                '    desk.admit("b", 2)\n'
                '    desk.admit("c", 5)\n'
                "    assert desk.count(2) == 2\n"
                "    assert desk.count(5) == 1\n"
                "    assert desk.count(9) == 0\n\n\n"
                "def test_next_regression():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("low", 1)\n'
                '    desk.admit("high", 7)\n'
                '    assert desk.next_job() == "high"\n'
                "    assert desk.count(7) == 0\n"
            ),
            "ops": [("replace", "desk.py", _d3_old, _d3_new)],
            "expect_targets": {"desk.py"},
        },
        {
            "instruction": (
                "console.py 新增 board()：返回各 level 当前排队数的字典（需要补充 import）。"
            ),
            "tests": (
                "import desk\n"
                "import console\n\n\n"
                "def test_board():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("a", 2)\n'
                '    desk.admit("b", 2)\n'
                '    desk.admit("c", 5)\n'
                "    assert console.board() == {2: 2, 5: 1}\n\n\n"
                "def test_board_empty():\n"
                "    desk.BUCKETS.clear()\n"
                "    assert console.board() == {}\n\n\n"
                "def test_show_regression():\n"
                '    assert console.show("j1") == "job=j1"\n'
            ),
            "ops": [
                ("replace", "console.py", _d4a_old, _d4a_new),
                ("replace", "console.py", _d4b_old, _d4b_new),
            ],
            "expect_targets": {"console.py"},
        },
        {
            "instruction": (
                "desk.py 新增 drain(level, n)：从指定 level 连续取出至多 n 个任务并返回列表"
                "（该 level 不存在或不足时返回已有部分）。"
            ),
            "tests": (
                "import desk\n"
                "import console\n\n\n"
                "def test_drain():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("a", 3)\n'
                '    desk.admit("b", 3)\n'
                '    desk.admit("c", 3)\n'
                '    assert desk.drain(3, 2) == ["a", "b"]\n'
                "    assert desk.count(3) == 1\n\n\n"
                "def test_drain_missing_level():\n"
                "    desk.BUCKETS.clear()\n"
                "    assert desk.drain(8, 3) == []\n\n\n"
                "def test_board_regression():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("a", 1)\n'
                "    assert console.board() == {1: 1}\n"
            ),
            "ops": [("replace", "desk.py", _d5_old, _d5_new)],
            "expect_targets": {"desk.py"},
        },
        {
            "instruction": (
                "请修改 desk.py 中的 admit：level 省略时改用 rules.py 的 DEFAULT_LEVEL 入队"
                "（显式传 level 的行为不变，需要补充 import）。"
            ),
            "tests": (
                "import desk\n"
                "import pytest\n\n\n"
                "def test_default_level():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("auto")\n'
                "    assert desk.count(1) == 1\n"
                '    assert desk.next_job() == "auto"\n\n\n'
                "def test_explicit_level_regression():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("x", 6)\n'
                "    assert desk.count(6) == 1\n\n\n"
                "def test_bounds_regression():\n"
                "    desk.BUCKETS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        desk.admit("bad", 99)\n'
            ),
            "ops": [
                ("replace", "desk.py", _d6a_old, _d6a_new),
                ("replace", "desk.py", _d6b_old, _d6b_new),
            ],
            "expect_targets": {"desk.py", "rules.py"},
        },
        {
            "instruction": (
                "desk.py 新增 levels()：返回当前仍有任务的 level 列表，按数值从大到小排列。"
            ),
            "tests": (
                "import desk\n\n\n"
                "def test_levels():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("a", 2)\n'
                '    desk.admit("b", 7)\n'
                '    desk.admit("c", 2)\n'
                "    assert desk.levels() == [7, 2]\n\n\n"
                "def test_levels_skips_empty():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("a", 4)\n'
                "    desk.next_job()\n"
                "    assert desk.levels() == []\n\n\n"
                "def test_drain_regression():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("a", 3)\n'
                '    desk.admit("b", 3)\n'
                '    assert desk.drain(3, 5) == ["a", "b"]\n'
            ),
            "ops": [("replace", "desk.py", _d7_old, _d7_new)],
            "expect_targets": {"desk.py"},
        },
        {
            "instruction": (
                "请修改 desk.py 中的 admit：越界 level 不再抛错，"
                "改为钳制到 MIN_LEVEL 与 MAX_LEVEL 边界值后入队（原拒绝行为废止）。"
            ),
            "tests": (
                "import desk\n\n\n"
                "def test_clamp_high():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("x", 99)\n'
                "    assert desk.count(9) == 1\n"
                '    assert desk.next_job() == "x"\n\n\n'
                "def test_clamp_low():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("y", -5)\n'
                "    assert desk.count(0) == 1\n\n\n"
                "def test_levels_regression():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("a", 2)\n'
                '    desk.admit("b", 7)\n'
                "    assert desk.levels() == [7, 2]\n"
            ),
            "ops": [("replace", "desk.py", _d8_old, _d8_new)],
            "expect_targets": {"desk.py"},
        },
        {
            "instruction": (
                "请修改 desk.py 中的 next_job：某 level 的最后一个任务被取走后，"
                "该空桶应从 BUCKETS 中删除（其他行为不变）。"
            ),
            "tests": (
                "import desk\n\n\n"
                "def test_empty_bucket_removed():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("solo", 5)\n'
                '    assert desk.next_job() == "solo"\n'
                "    assert 5 not in desk.BUCKETS\n\n\n"
                "def test_partial_bucket_kept():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("a", 5)\n'
                '    desk.admit("b", 5)\n'
                '    assert desk.next_job() == "a"\n'
                "    assert 5 in desk.BUCKETS\n"
                "    assert desk.count(5) == 1\n\n\n"
                "def test_clamp_regression():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("x", 99)\n'
                "    assert desk.count(9) == 1\n"
            ),
            "ops": [("replace", "desk.py", _d9_old, _d9_new)],
            "expect_targets": {"desk.py"},
        },
        {
            "instruction": (
                "请修改 rules.py 中的 DEFAULT_LEVEL：应从 1 改为 7，"
                "使省略 level 的入队任务落到 7。"
            ),
            "tests": (
                "import desk\n"
                "import rules\n"
                "import console\n\n\n"
                "def test_default_now_seven():\n"
                "    assert rules.DEFAULT_LEVEL == 7\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("auto")\n'
                "    assert desk.count(7) == 1\n"
                '    assert desk.next_job() == "auto"\n\n\n'
                "def test_full_chain():\n"
                "    desk.BUCKETS.clear()\n"
                '    desk.admit("low", 1)\n'
                '    desk.admit("high", 7)\n'
                '    assert desk.next_job() == "high"\n'
                '    assert desk.next_job() == "low"\n'
                '    desk.admit("a", 3)\n'
                '    desk.admit("b", 3)\n'
                '    assert desk.drain(3, 1) == ["a"]\n'
                "    assert desk.levels() == [3]\n"
                "    assert console.board() == {3: 1}\n"
            ),
            "ops": [("replace", "rules.py", "DEFAULT_LEVEL = 1\n", "DEFAULT_LEVEL = 7\n")],
            "expect_targets": {"rules.py"},
        },
    ],
    info_points=[
        {"id": "ip_bucket_order", "type": "implementation",
         "value": "next_job 按 level 降序、桶内先入先出",
         "locator": "instruction:step1 + desk.py",
         "needed_by_steps": [1, 7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_level_bounds", "type": "critical_data",
         "value": "MIN_LEVEL=0、MAX_LEVEL=9（数值只在 rules.py）",
         "locator": "rules.py（指令只给符号名）",
         "needed_by_steps": [2, 8],
         "redundant_in_instruction": False},
        {"id": "ip_default_level", "type": "critical_data",
         "value": "DEFAULT_LEVEL：1（step6 起）→ 7（step10）",
         "locator": "instruction:step6 + instruction:step10 + rules.py",
         "needed_by_steps": [6, 10],
         "redundant_in_instruction": True},
        {"id": "ip_clamp_rule", "type": "history",
         "value": "越界钳制取代拒绝（step8 决策）",
         "locator": "desk.py after step8 + step9 回归 eval",
         "needed_by_steps": [8, 9],
         "redundant_in_instruction": False},
        {"id": "ip_bucket_cleanup", "type": "interface",
         "value": "取空后删除空桶",
         "locator": "instruction:step9 + desk.py",
         "needed_by_steps": [9, 10],
         "redundant_in_instruction": True},
    ],
)

# ============================================================ LF2 ind_long_ledger
# 变体 a：条目列表记账（余额→档位费率→窗口合计→规则两次改约传播）

_led_a = (
    '"""Ledger."""\n\n\n'
    "ENTRIES = []\n\n\n"
    "def post(amount):\n"
    "    ENTRIES.append(amount)\n"
)
_rates_a = (
    '"""Rate tiers."""\n\n\n'
    "TIER1_LIMIT = 100\n"
    "TIER1_RATE = 1\n"
    "TIER2_RATE = 2\n"
)
_aud_a = (
    '"""Audit lines."""\n\n\n'
    "def line(amount):\n"
    '    return f"amt={amount}"\n'
)
_e1_old = "def post(amount):\n    ENTRIES.append(amount)"
_e1_new = _e1_old + "\n\n\ndef balance():\n    return sum(ENTRIES)"
_e2_old = _e1_old
_e2_new = (
    "def post(amount):\n"
    "    if amount <= 0:\n"
    '        raise ValueError("amount")\n'
    "    ENTRIES.append(amount)"
)
_e3a_old = '"""Ledger."""'
_e3a_new = '"""Ledger."""\nimport rates'
_e3b_old = "def balance():\n    return sum(ENTRIES)"
_e3b_new = _e3b_old + (
    "\n\n\ndef fee(amount):\n"
    "    if amount < rates.TIER1_LIMIT:\n"
    "        return amount * rates.TIER1_RATE\n"
    "    return amount * rates.TIER2_RATE"
)
_e4_old = (
    "def fee(amount):\n"
    "    if amount < rates.TIER1_LIMIT:\n"
    "        return amount * rates.TIER1_RATE\n"
    "    return amount * rates.TIER2_RATE"
)
_e4_new = _e4_old + "\n\n\ndef window_total(n):\n    return sum(ENTRIES[-n:])"
_e5a_old = '"""Audit lines."""'
_e5a_new = '"""Audit lines."""\nfrom ledger import fee'
_e5b_old = 'def line(amount):\n    return f"amt={amount}"'
_e5b_new = _e5b_old + (
    '\n\n\ndef fee_line(amount):\n'
    '    return f"fee={fee(amount)}"'
)
_e7_old = "def window_total(n):\n    return sum(ENTRIES[-n:])"
_e7_new = _e7_old + (
    "\n\n\ndef average():\n"
    "    if not ENTRIES:\n"
    "        return 0\n"
    "    return sum(ENTRIES) / len(ENTRIES)"
)
_e8_old = (
    "    if amount < rates.TIER1_LIMIT:\n"
    "        return amount * rates.TIER1_RATE\n"
    "    return amount * rates.TIER2_RATE"
)
_e8_new = (
    "    if amount <= rates.TIER1_LIMIT:\n"
    "        return amount * rates.TIER1_RATE\n"
    "    return amount * rates.TIER2_RATE"
)
_e9_old = "def window_total(n):\n    return sum(ENTRIES[-n:])"
_e9_new = (
    "def window_total(n):\n"
    "    if n <= 0:\n"
    "        return 0\n"
    "    return sum(ENTRIES[-n:])"
)
T(
    id="ind_L02a",
    family="ind_long_ledger",
    type="billing_engine_evolution",
    difficulty="long",
    focus="10 步记账引擎演进：余额→入账校验→档位费率→窗口合计→审计消费方→两次费率改约传播",
    files={"ledger.py": _led_a, "rates.py": _rates_a, "audit.py": _aud_a},
    steps=[
        {
            "instruction": (
                "ledger.py 新增 balance()：返回 ENTRIES 中所有金额之和（空账返回 0）。"
            ),
            "tests": (
                "import ledger\n\n\n"
                "def test_balance():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(50)\n"
                "    ledger.post(30)\n"
                "    assert ledger.balance() == 80\n\n\n"
                "def test_balance_empty():\n"
                "    ledger.ENTRIES.clear()\n"
                "    assert ledger.balance() == 0\n\n\n"
                "def test_post_regression():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(7)\n"
                "    assert ledger.ENTRIES == [7]\n"
            ),
            "ops": [("replace", "ledger.py", _e1_old, _e1_new)],
            "expect_targets": {"ledger.py"},
        },
        {
            "instruction": (
                "请修改 ledger.py 中的 post：amount 小于等于 0 时抛 ValueError"
                "（正常入账行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import ledger\n\n\n"
                "def test_reject_nonpositive():\n"
                "    ledger.ENTRIES.clear()\n"
                "    with pytest.raises(ValueError):\n"
                "        ledger.post(0)\n"
                "    with pytest.raises(ValueError):\n"
                "        ledger.post(-5)\n\n\n"
                "def test_post_ok():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(40)\n"
                "    assert ledger.balance() == 40\n"
            ),
            "ops": [("replace", "ledger.py", _e2_old, _e2_new)],
            "expect_targets": {"ledger.py"},
        },
        {
            "instruction": (
                "ledger.py 新增 fee(amount)：amount 小于档位常量 TIER1_LIMIT 时按 TIER1_RATE "
                "计费，否则按 TIER2_RATE 计费（档位常量从 rates 模块导入）。"
            ),
            "tests": (
                "import ledger\n\n\n"
                "def test_fee_tier1():\n"
                "    assert ledger.fee(50) == 50\n\n\n"
                "def test_fee_tier2():\n"
                "    assert ledger.fee(150) == 300\n\n\n"
                "def test_post_regression():\n"
                "    import pytest\n"
                "    ledger.ENTRIES.clear()\n"
                "    with pytest.raises(ValueError):\n"
                "        ledger.post(-1)\n"
                "    ledger.post(10)\n"
                "    assert ledger.balance() == 10\n"
            ),
            "ops": [
                ("replace", "ledger.py", _e3a_old, _e3a_new),
                ("replace", "ledger.py", _e3b_old, _e3b_new),
            ],
            "expect_targets": {"ledger.py"},
        },
        {
            "instruction": (
                "ledger.py 新增 window_total(n)：返回最近 n 笔入账之和；"
                "n 大于现有笔数时返回全部之和。"
            ),
            "tests": (
                "import ledger\n\n\n"
                "def test_window():\n"
                "    ledger.ENTRIES.clear()\n"
                "    for x in (10, 20, 30, 40):\n"
                "        ledger.post(x)\n"
                "    assert ledger.window_total(2) == 70\n\n\n"
                "def test_window_larger_than_size():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(5)\n"
                "    ledger.post(6)\n"
                "    assert ledger.window_total(10) == 11\n\n\n"
                "def test_fee_regression():\n"
                "    assert ledger.fee(50) == 50\n"
                "    assert ledger.fee(150) == 300\n"
            ),
            "ops": [("replace", "ledger.py", _e4_old, _e4_new)],
            "expect_targets": {"ledger.py"},
        },
        {
            "instruction": (
                "audit.py 新增 fee_line(amount)：调用 ledger.py 的 fee 计算并输出 "
                "'fee=X'（需要补充 import）。"
            ),
            "tests": (
                "import audit\n"
                "import ledger\n\n\n"
                "def test_fee_line():\n"
                "    assert audit.fee_line(50) == \"fee=50\"\n"
                "    assert audit.fee_line(150) == \"fee=300\"\n\n\n"
                "def test_line_regression():\n"
                "    assert audit.line(9) == \"amt=9\"\n\n\n"
                "def test_window_regression():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(1)\n"
                "    ledger.post(2)\n"
                "    assert ledger.window_total(1) == 2\n"
            ),
            "ops": [
                ("replace", "audit.py", _e5a_old, _e5a_new),
                ("replace", "audit.py", _e5b_old, _e5b_new),
            ],
            "expect_targets": {"audit.py", "ledger.py"},
        },
        {
            "instruction": (
                "请修改 rates.py 中的 TIER2_RATE：应从 2 改为 3，计费与审计输出随之更新。"
            ),
            "tests": (
                "import rates\n"
                "import ledger\n"
                "import audit\n\n\n"
                "def test_tier2_rate_updated():\n"
                "    assert rates.TIER2_RATE == 3\n"
                "    assert ledger.fee(150) == 450\n"
                "    assert audit.fee_line(150) == \"fee=450\"\n\n\n"
                "def test_tier1_regression():\n"
                "    assert ledger.fee(50) == 50\n"
                "    assert ledger.fee(99) == 99\n"
            ),
            "ops": [("replace", "rates.py", "TIER2_RATE = 2\n", "TIER2_RATE = 3\n")],
            "expect_targets": {"rates.py"},
        },
        {
            "instruction": (
                "ledger.py 新增 average()：余额除以笔数，空账返回 0。"
            ),
            "tests": (
                "import ledger\n\n\n"
                "def test_average():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(10)\n"
                "    ledger.post(30)\n"
                "    assert ledger.average() == 20\n\n\n"
                "def test_average_empty():\n"
                "    ledger.ENTRIES.clear()\n"
                "    assert ledger.average() == 0\n\n\n"
                "def test_fee_regression():\n"
                "    assert ledger.fee(150) == 450\n"
            ),
            "ops": [("replace", "ledger.py", _e7_old, _e7_new)],
            "expect_targets": {"ledger.py"},
        },
        {
            "instruction": (
                "请修改 ledger.py 中的 fee：amount 恰好等于 TIER1_LIMIT 时也按 TIER1_RATE "
                "计费（当前实现把该值划入高费率档）。"
            ),
            "tests": (
                "import ledger\n\n\n"
                "def test_boundary_inclusive():\n"
                "    assert ledger.fee(100) == 100\n\n\n"
                "def test_below_boundary():\n"
                "    assert ledger.fee(99) == 99\n\n\n"
                "def test_above_boundary():\n"
                "    assert ledger.fee(101) == 303\n\n\n"
                "def test_average_regression():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(10)\n"
                "    ledger.post(30)\n"
                "    assert ledger.average() == 20\n"
            ),
            "ops": [("replace", "ledger.py", _e8_old, _e8_new)],
            "expect_targets": {"ledger.py"},
        },
        {
            "instruction": (
                "请修改 ledger.py 中的 window_total：n 小于等于 0 时应返回 0"
                "（正数行为不变）。"
            ),
            "tests": (
                "import ledger\n\n\n"
                "def test_window_zero():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(10)\n"
                "    ledger.post(20)\n"
                "    assert ledger.window_total(0) == 0\n\n\n"
                "def test_window_negative():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(10)\n"
                "    assert ledger.window_total(-3) == 0\n\n\n"
                "def test_window_positive_regression():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(10)\n"
                "    ledger.post(20)\n"
                "    assert ledger.window_total(1) == 20\n"
            ),
            "ops": [("replace", "ledger.py", _e9_old, _e9_new)],
            "expect_targets": {"ledger.py"},
        },
        {
            "instruction": (
                "请修改 rates.py 中的 TIER1_RATE：应从 1 改为 2，档位计费随之更新"
                "（TIER2_RATE 上一轮的改约仍然生效）。"
            ),
            "tests": (
                "import rates\n"
                "import ledger\n"
                "import audit\n\n\n"
                "def test_tier1_rate_updated():\n"
                "    assert rates.TIER1_RATE == 2\n"
                "    assert ledger.fee(50) == 100\n"
                "    assert ledger.fee(150) == 450\n"
                "    assert audit.fee_line(50) == \"fee=100\"\n\n\n"
                "def test_full_chain():\n"
                "    ledger.ENTRIES.clear()\n"
                "    ledger.post(60)\n"
                "    ledger.post(40)\n"
                "    assert ledger.balance() == 100\n"
                "    assert ledger.window_total(1) == 40\n"
                "    assert ledger.average() == 50\n"
                "    assert ledger.fee(100) == 200\n"
            ),
            "ops": [("replace", "rates.py", "TIER1_RATE = 1\n", "TIER1_RATE = 2\n")],
            "expect_targets": {"rates.py"},
        },
    ],
    info_points=[
        {"id": "ip_balance_def", "type": "implementation",
         "value": "balance = sum(ENTRIES)",
         "locator": "instruction:step1 + ledger.py",
         "needed_by_steps": [1, 7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_fee_tiers", "type": "implementation",
         "value": "amount 不超过 TIER1_LIMIT 用 TIER1_RATE，否则 TIER2_RATE",
         "locator": "instruction:step3 + instruction:step8",
         "needed_by_steps": [3, 5, 6, 8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_window_rule", "type": "interface",
         "value": "window_total(n) 取最近 n 笔；n<=0 返回 0",
         "locator": "instruction:step4 + instruction:step9",
         "needed_by_steps": [4, 9],
         "redundant_in_instruction": True},
        {"id": "ip_rates_dynamic", "type": "history",
         "value": "ledger 以 import rates 动态引用档位常量",
         "locator": "ledger.py after step3 + assistant history",
         "needed_by_steps": [6, 10],
         "redundant_in_instruction": False},
        {"id": "ip_rate_changes", "type": "critical_data",
         "value": "TIER2_RATE 2→3（step6）、TIER1_RATE 1→2（step10）",
         "locator": "instruction:step6 + instruction:step10",
         "needed_by_steps": [6, 10],
         "redundant_in_instruction": True},
    ],
)

# 变体 b：按日用量记账（字典累加→超额计费→峰值→日期校验→额度二次改约）

_met_b = (
    '"""Usage meter."""\n\n\n'
    "USAGE = {}\n\n\n"
    "def record(day, units):\n"
    "    USAGE[day] = USAGE.get(day, 0) + units\n"
)
_pri_b = (
    '"""Price table."""\n\n\n'
    "UNIT_PRICE = 5\n"
    "FREE_QUOTA = 20\n"
)
_bil_b = (
    '"""Billing summary."""\n\n\n'
    "def header():\n"
    '    return "bill"\n'
)
_u1_old = "def record(day, units):\n    USAGE[day] = USAGE.get(day, 0) + units"
_u1_new = _u1_old + "\n\n\ndef total_units():\n    return sum(USAGE.values())"
_u2_old = _u1_old
_u2_new = (
    "def record(day, units):\n"
    "    if units < 0:\n"
    '        raise ValueError("units")\n'
    "    USAGE[day] = USAGE.get(day, 0) + units"
)
_u3a_old = '"""Usage meter."""'
_u3a_new = '"""Usage meter."""\nimport prices'
_u3b_old = "def total_units():\n    return sum(USAGE.values())"
_u3b_new = _u3b_old + (
    "\n\n\ndef day_charge(day):\n"
    "    usage = USAGE.get(day, 0)\n"
    "    return max(usage - prices.FREE_QUOTA, 0) * prices.UNIT_PRICE"
)
_u4_old = (
    "def day_charge(day):\n"
    "    usage = USAGE.get(day, 0)\n"
    "    return max(usage - prices.FREE_QUOTA, 0) * prices.UNIT_PRICE"
)
_u4_new = _u4_old + (
    "\n\n\ndef days_over():\n"
    "    return sorted(d for d in USAGE if USAGE[d] > prices.FREE_QUOTA)"
)
_u5a_old = '"""Billing summary."""'
_u5a_new = '"""Billing summary."""\nfrom meter import day_charge'
_u5b_old = 'def header():\n    return "bill"'
_u5b_new = _u5b_old + (
    '\n\n\ndef charge_line(day):\n'
    '    return f"day={day} charge={day_charge(day)}"'
)
_u7_old = (
    "def days_over():\n"
    "    return sorted(d for d in USAGE if USAGE[d] > prices.FREE_QUOTA)"
)
_u7_new = _u7_old + (
    "\n\n\ndef peak():\n"
    "    if not USAGE:\n"
    "        return None\n"
    "    best = max(USAGE.values())\n"
    "    return min(d for d in USAGE if USAGE[d] == best)"
)
_u8_old = (
    "def record(day, units):\n"
    "    if units < 0:\n"
    '        raise ValueError("units")\n'
    "    USAGE[day] = USAGE.get(day, 0) + units"
)
_u8_new = (
    "def record(day, units):\n"
    "    if units < 0:\n"
    '        raise ValueError("units")\n'
    '    if len(day) != 10 or day[4] != "-" or day[7] != "-":\n'
    '        raise ValueError("day")\n'
    "    if not (day[:4].isdigit() and day[5:7].isdigit() and day[8:10].isdigit()):\n"
    '        raise ValueError("day")\n'
    "    USAGE[day] = USAGE.get(day, 0) + units"
)
_u9a_old = "from meter import day_charge"
_u9a_new = "from meter import day_charge, USAGE"
_u9b_old = (
    "def charge_line(day):\n"
    '    return f"day={day} charge={day_charge(day)}"'
)
_u9b_new = _u9b_old + (
    "\n\n\ndef total_charge():\n"
    "    return sum(day_charge(d) for d in USAGE)"
)
T(
    id="ind_L02b",
    family="ind_long_ledger",
    type="billing_engine_evolution",
    difficulty="long",
    focus="10 步用量记账演进：累加→校验→超额计费→超额日→消费方→涨价改约→峰值→日期边界→额度二次改约",
    files={"meter.py": _met_b, "prices.py": _pri_b, "billing.py": _bil_b},
    steps=[
        {
            "instruction": (
                "meter.py 新增 total_units()：返回 USAGE 中所有用量之和（空表返回 0）。"
            ),
            "tests": (
                "import meter\n\n\n"
                "def test_total():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 10)\n'
                '    meter.record("2024-01-02", 5)\n'
                "    assert meter.total_units() == 15\n\n\n"
                "def test_total_empty():\n"
                "    meter.USAGE.clear()\n"
                "    assert meter.total_units() == 0\n\n\n"
                "def test_record_regression():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 3)\n'
                '    assert meter.USAGE["2024-01-01"] == 3\n'
            ),
            "ops": [("replace", "meter.py", _u1_old, _u1_new)],
            "expect_targets": {"meter.py"},
        },
        {
            "instruction": (
                "请修改 meter.py 中的 record：units 小于 0 时抛 ValueError"
                "（正常记录行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import meter\n\n\n"
                "def test_reject_negative():\n"
                "    meter.USAGE.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        meter.record("2024-01-01", -1)\n\n\n'
                "def test_record_ok():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 4)\n'
                "    assert meter.total_units() == 4\n"
            ),
            "ops": [("replace", "meter.py", _u2_old, _u2_new)],
            "expect_targets": {"meter.py"},
        },
        {
            "instruction": (
                "meter.py 新增 day_charge(day)：用量超出 FREE_QUOTA 的部分按 UNIT_PRICE "
                "计费，未超出返回 0（价格常量从 prices 模块导入）。"
            ),
            "tests": (
                "import meter\n\n\n"
                "def test_charge_over():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 25)\n'
                '    assert meter.day_charge("2024-01-01") == 25\n\n\n'
                "def test_charge_under():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 10)\n'
                '    assert meter.day_charge("2024-01-01") == 0\n\n\n'
                "def test_charge_missing_day():\n"
                "    meter.USAGE.clear()\n"
                '    assert meter.day_charge("2024-01-09") == 0\n\n\n'
                "def test_total_regression():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 6)\n'
                "    assert meter.total_units() == 6\n"
            ),
            "ops": [
                ("replace", "meter.py", _u3a_old, _u3a_new),
                ("replace", "meter.py", _u3b_old, _u3b_new),
            ],
            "expect_targets": {"meter.py"},
        },
        {
            "instruction": (
                "meter.py 新增 days_over()：返回用量超出 FREE_QUOTA 的 day 列表，"
                "按 day 升序排列。"
            ),
            "tests": (
                "import meter\n\n\n"
                "def test_days_over():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-03", 30)\n'
                '    meter.record("2024-01-01", 21)\n'
                '    meter.record("2024-01-02", 5)\n'
                '    assert meter.days_over() == ["2024-01-01", "2024-01-03"]\n\n\n'
                "def test_days_over_empty():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 1)\n'
                "    assert meter.days_over() == []\n\n\n"
                "def test_charge_regression():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 25)\n'
                '    assert meter.day_charge("2024-01-01") == 25\n'
            ),
            "ops": [("replace", "meter.py", _u4_old, _u4_new)],
            "expect_targets": {"meter.py"},
        },
        {
            "instruction": (
                "billing.py 新增 charge_line(day)：调用 meter.py 的 day_charge 计算并输出 "
                "'day=X charge=Y'（需要补充 import）。"
            ),
            "tests": (
                "import billing\n"
                "import meter\n\n\n"
                "def test_charge_line():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 25)\n'
                '    assert billing.charge_line("2024-01-01") == "day=2024-01-01 charge=25"\n\n\n'
                "def test_header_regression():\n"
                '    assert billing.header() == "bill"\n\n\n'
                "def test_days_over_regression():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-05", 40)\n'
                '    assert meter.days_over() == ["2024-01-05"]\n'
            ),
            "ops": [
                ("replace", "billing.py", _u5a_old, _u5a_new),
                ("replace", "billing.py", _u5b_old, _u5b_new),
            ],
            "expect_targets": {"billing.py", "meter.py"},
        },
        {
            "instruction": (
                "请修改 prices.py 中的 UNIT_PRICE：应从 5 改为 8，超额计费随之更新。"
            ),
            "tests": (
                "import prices\n"
                "import meter\n"
                "import billing\n\n\n"
                "def test_price_updated():\n"
                "    assert prices.UNIT_PRICE == 8\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 25)\n'
                '    assert meter.day_charge("2024-01-01") == 40\n'
                '    assert billing.charge_line("2024-01-01") == "day=2024-01-01 charge=40"\n\n\n'
                "def test_under_quota_regression():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 10)\n'
                '    assert meter.day_charge("2024-01-01") == 0\n'
            ),
            "ops": [("replace", "prices.py", "UNIT_PRICE = 5\n", "UNIT_PRICE = 8\n")],
            "expect_targets": {"prices.py"},
        },
        {
            "instruction": (
                "meter.py 新增 peak()：返回用量最大的 day（并列时取 day 较小者），"
                "USAGE 为空返回 None。"
            ),
            "tests": (
                "import meter\n\n\n"
                "def test_peak():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-02", 12)\n'
                '    meter.record("2024-01-01", 30)\n'
                '    meter.record("2024-01-03", 30)\n'
                '    assert meter.peak() == "2024-01-01"\n\n\n'
                "def test_peak_empty():\n"
                "    meter.USAGE.clear()\n"
                "    assert meter.peak() is None\n\n\n"
                "def test_charge_regression():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 25)\n'
                '    assert meter.day_charge("2024-01-01") == 40\n'
            ),
            "ops": [("replace", "meter.py", _u7_old, _u7_new)],
            "expect_targets": {"meter.py"},
        },
        {
            "instruction": (
                "请修改 meter.py 中的 record：day 必须形如 2024-01-01 的 10 位日期"
                "（第 5、8 位为短横且其余为数字），否则抛 ValueError。"
            ),
            "tests": (
                "import pytest\n"
                "import meter\n\n\n"
                "def test_bad_day_format():\n"
                "    meter.USAGE.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        meter.record("jan-1", 5)\n'
                "    with pytest.raises(ValueError):\n"
                '        meter.record("2024/01/01", 5)\n\n\n'
                "def test_good_day_format():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 5)\n'
                '    assert meter.USAGE["2024-01-01"] == 5\n\n\n'
                "def test_peak_regression():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-02", 9)\n'
                '    assert meter.peak() == "2024-01-02"\n'
            ),
            "ops": [("replace", "meter.py", _u8_old, _u8_new)],
            "expect_targets": {"meter.py"},
        },
        {
            "instruction": (
                "billing.py 新增 total_charge()：对所有已记录日期的计费结果求和并返回"
                "（需要补充 import）。"
            ),
            "tests": (
                "import billing\n"
                "import meter\n\n\n"
                "def test_total_charge():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 25)\n'
                '    meter.record("2024-01-02", 30)\n'
                "    assert billing.total_charge() == 120\n\n\n"
                "def test_total_charge_empty():\n"
                "    meter.USAGE.clear()\n"
                "    assert billing.total_charge() == 0\n\n\n"
                "def test_charge_line_regression():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 25)\n'
                '    assert billing.charge_line("2024-01-01") == "day=2024-01-01 charge=40"\n'
            ),
            "ops": [
                ("replace", "billing.py", _u9a_old, _u9a_new),
                ("replace", "billing.py", _u9b_old, _u9b_new),
            ],
            "expect_targets": {"billing.py"},
        },
        {
            "instruction": (
                "请修改 prices.py 中的 FREE_QUOTA：应从 20 改为 30，超额判定随之更新"
                "（UNIT_PRICE 上一轮的改约仍然生效）。"
            ),
            "tests": (
                "import prices\n"
                "import meter\n"
                "import billing\n\n\n"
                "def test_quota_updated():\n"
                "    assert prices.FREE_QUOTA == 30\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 25)\n'
                '    assert meter.day_charge("2024-01-01") == 0\n'
                "    assert meter.days_over() == []\n\n\n"
                "def test_full_chain():\n"
                "    meter.USAGE.clear()\n"
                '    meter.record("2024-01-01", 40)\n'
                '    meter.record("2024-01-02", 10)\n'
                "    assert meter.total_units() == 50\n"
                '    assert meter.peak() == "2024-01-01"\n'
                '    assert meter.days_over() == ["2024-01-01"]\n'
                '    assert meter.day_charge("2024-01-01") == 80\n'
                "    assert billing.total_charge() == 80\n"
                '    assert billing.charge_line("2024-01-01") == "day=2024-01-01 charge=80"\n'
            ),
            "ops": [("replace", "prices.py", "FREE_QUOTA = 20\n", "FREE_QUOTA = 30\n")],
            "expect_targets": {"prices.py"},
        },
    ],
    info_points=[
        {"id": "ip_record_contract", "type": "interface",
         "value": "record(day, units) 累加用量；负 units 拒绝",
         "locator": "instruction:step1 + instruction:step2",
         "needed_by_steps": [1, 2, 8],
         "redundant_in_instruction": True},
        {"id": "ip_charge_formula", "type": "implementation",
         "value": "max(usage - FREE_QUOTA, 0) * UNIT_PRICE",
         "locator": "instruction:step3 + meter.py",
         "needed_by_steps": [3, 5, 6, 9, 10],
         "redundant_in_instruction": True},
        {"id": "ip_price_changes", "type": "critical_data",
         "value": "UNIT_PRICE 5→8（step6）、FREE_QUOTA 20→30（step10）",
         "locator": "instruction:step6 + instruction:step10",
         "needed_by_steps": [6, 10],
         "redundant_in_instruction": True},
        {"id": "ip_usage_shape", "type": "history",
         "value": "USAGE 为 {day: units} 字典",
         "locator": "meter.py after step1 + assistant history",
         "needed_by_steps": [3, 4, 7, 9],
         "redundant_in_instruction": False},
        {"id": "ip_prices_dynamic", "type": "history",
         "value": "meter 以 import prices 动态引用价格常量",
         "locator": "meter.py after step3 + assistant history",
         "needed_by_steps": [6, 10],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ LF3 ind_long_warehouse
# 变体 a：字典库存（入库→查询→预留→释放→回补阈值两次改约）

_stk_a = (
    '"""Stock records."""\n\n\n'
    "ITEMS = {}\n\n\n"
    "def receive(sku, qty):\n"
    "    ITEMS[sku] = ITEMS.get(sku, 0) + qty\n"
)
_trm_a = (
    '"""Stock terms."""\n\n\n'
    "BACKORDER_MIN = 5\n"
)
_shp_a = (
    '"""Shipping notes."""\n\n\n'
    "def note(sku):\n"
    '    return f"sku={sku}"\n'
)
_s1_old = "def receive(sku, qty):\n    ITEMS[sku] = ITEMS.get(sku, 0) + qty"
_s1_new = _s1_old + "\n\n\ndef available(sku):\n    return ITEMS.get(sku, 0)"
_s2_old = _s1_old
_s2_new = (
    "def receive(sku, qty):\n"
    "    if qty <= 0:\n"
    '        raise ValueError("qty")\n'
    "    ITEMS[sku] = ITEMS.get(sku, 0) + qty"
)
_s3_old = "def available(sku):\n    return ITEMS.get(sku, 0)"
_s3_new = _s3_old + (
    "\n\n\ndef reserve(sku, qty):\n"
    "    have = ITEMS.get(sku, 0)\n"
    "    if have < qty:\n"
    "        return False\n"
    "    ITEMS[sku] = have - qty\n"
    "    return True"
)
_s4_old = (
    "def reserve(sku, qty):\n"
    "    have = ITEMS.get(sku, 0)\n"
    "    if have < qty:\n"
    "        return False\n"
    "    ITEMS[sku] = have - qty\n"
    "    return True"
)
_s4_new = _s4_old + (
    "\n\n\ndef release(sku, qty):\n"
    "    ITEMS[sku] = ITEMS.get(sku, 0) + qty\n"
    "    return ITEMS[sku]"
)
_s5a_old = '"""Shipping notes."""'
_s5a_new = '"""Shipping notes."""\nimport stock'
_s5b_old = 'def note(sku):\n    return f"sku={sku}"'
_s5b_new = _s5b_old + (
    "\n\n\ndef reservation_line(sku, qty):\n"
    "    if stock.reserve(sku, qty):\n"
    '        return f"held={sku}"\n'
    '    return f"short={sku}"'
)
_s7a_old = '"""Stock records."""'
_s7a_new = '"""Stock records."""\nfrom terms import BACKORDER_MIN'
_s7b_old = (
    "def release(sku, qty):\n"
    "    ITEMS[sku] = ITEMS.get(sku, 0) + qty\n"
    "    return ITEMS[sku]"
)
_s7b_new = _s7b_old + (
    "\n\n\ndef backorder_qty(sku):\n"
    "    lack = BACKORDER_MIN - available(sku)\n"
    "    return lack if lack > 0 else 0"
)
_s8_old = (
    "def reserve(sku, qty):\n"
    "    have = ITEMS.get(sku, 0)\n"
    "    if have < qty:\n"
    "        return False\n"
    "    ITEMS[sku] = have - qty\n"
    "    return True"
)
_s8_new = (
    "def reserve(sku, qty):\n"
    "    if qty <= 0:\n"
    '        raise ValueError("qty")\n'
    "    have = ITEMS.get(sku, 0)\n"
    "    if have < qty:\n"
    "        return False\n"
    "    ITEMS[sku] = have - qty\n"
    "    return True"
)
_s9_old = (
    "def backorder_qty(sku):\n"
    "    lack = BACKORDER_MIN - available(sku)\n"
    "    return lack if lack > 0 else 0"
)
_s9_new = _s9_old + (
    "\n\n\ndef low_stock():\n"
    "    return sorted(sku for sku in ITEMS if backorder_qty(sku) > 0)"
)
T(
    id="ind_L03a",
    family="ind_long_warehouse",
    type="inventory_reservation_evolution",
    difficulty="long",
    focus="10 步库存演进：入库→查询→预留→释放→出货消费方→回补阈值两次改约",
    files={"stock.py": _stk_a, "terms.py": _trm_a, "ship.py": _shp_a},
    steps=[
        {
            "instruction": (
                "stock.py 新增 available(sku)：返回该 sku 的现有数量（缺失返回 0）。"
            ),
            "tests": (
                "import stock\n\n\n"
                "def test_available():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 7)\n'
                '    assert stock.available("a") == 7\n\n\n'
                "def test_available_missing():\n"
                "    stock.ITEMS.clear()\n"
                '    assert stock.available("zz") == 0\n\n\n'
                "def test_receive_regression():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 2)\n'
                '    assert stock.ITEMS["a"] == 2\n'
            ),
            "ops": [("replace", "stock.py", _s1_old, _s1_new)],
            "expect_targets": {"stock.py"},
        },
        {
            "instruction": (
                "请修改 stock.py 中的 receive：qty 小于等于 0 时抛 ValueError"
                "（正常入库行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import stock\n\n\n"
                "def test_reject_nonpositive():\n"
                "    stock.ITEMS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        stock.receive("a", 0)\n'
                "    with pytest.raises(ValueError):\n"
                '        stock.receive("a", -3)\n\n\n'
                "def test_receive_ok():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 9)\n'
                '    assert stock.available("a") == 9\n'
            ),
            "ops": [("replace", "stock.py", _s2_old, _s2_new)],
            "expect_targets": {"stock.py"},
        },
        {
            "instruction": (
                "stock.py 新增 reserve(sku, qty)：可用量不少于 qty 时扣减并返回 True，"
                "否则返回 False 且不扣减。"
            ),
            "tests": (
                "import stock\n\n\n"
                "def test_reserve_success():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 10)\n'
                '    assert stock.reserve("a", 4) is True\n'
                '    assert stock.available("a") == 6\n\n\n'
                "def test_reserve_short():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 3)\n'
                '    assert stock.reserve("a", 5) is False\n'
                '    assert stock.available("a") == 3\n\n\n'
                "def test_receive_regression():\n"
                "    import pytest\n"
                "    stock.ITEMS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        stock.receive("a", -1)\n'
            ),
            "ops": [("replace", "stock.py", _s3_old, _s3_new)],
            "expect_targets": {"stock.py"},
        },
        {
            "instruction": (
                "stock.py 新增 release(sku, qty)：把 qty 加回该 sku 的可用量"
                "并返回新可用量。"
            ),
            "tests": (
                "import stock\n\n\n"
                "def test_release():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 10)\n'
                '    stock.reserve("a", 4)\n'
                '    assert stock.release("a", 4) == 10\n'
                '    assert stock.available("a") == 10\n\n\n'
                "def test_release_partial():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("b", 5)\n'
                '    stock.reserve("b", 2)\n'
                '    assert stock.release("b", 1) == 4\n\n\n'
                "def test_reserve_regression():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 3)\n'
                '    assert stock.reserve("a", 5) is False\n'
                '    assert stock.available("a") == 3\n'
            ),
            "ops": [("replace", "stock.py", _s4_old, _s4_new)],
            "expect_targets": {"stock.py"},
        },
        {
            "instruction": (
                "ship.py 新增 reservation_line(sku, qty)：调用 stock.py 的 reserve 预留，"
                "成功返回 'held=sku'，失败返回 'short=sku'（需要补充 import）。"
            ),
            "tests": (
                "import ship\n"
                "import stock\n\n\n"
                "def test_held():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 10)\n'
                '    assert ship.reservation_line("a", 4) == "held=a"\n'
                '    assert stock.available("a") == 6\n\n\n'
                "def test_short():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 2)\n'
                '    assert ship.reservation_line("a", 5) == "short=a"\n'
                '    assert stock.available("a") == 2\n\n\n'
                "def test_note_regression():\n"
                '    assert ship.note("x") == "sku=x"\n'
            ),
            "ops": [
                ("replace", "ship.py", _s5a_old, _s5a_new),
                ("replace", "ship.py", _s5b_old, _s5b_new),
            ],
            "expect_targets": {"ship.py", "stock.py"},
        },
        {
            "instruction": (
                "请修改 terms.py 中的 BACKORDER_MIN：应从 5 改为 10。"
            ),
            "tests": (
                "import terms\n"
                "import stock\n\n\n"
                "def test_min_updated():\n"
                "    assert terms.BACKORDER_MIN == 10\n\n\n"
                "def test_reserve_regression():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 10)\n'
                '    assert stock.reserve("a", 4) is True\n'
                '    assert stock.available("a") == 6\n\n\n'
                "def test_release_regression():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 5)\n'
                '    assert stock.release("a", 2) == 7\n'
            ),
            "ops": [("replace", "terms.py", "BACKORDER_MIN = 5\n", "BACKORDER_MIN = 10\n")],
            "expect_targets": {"terms.py"},
        },
        {
            "instruction": (
                "stock.py 新增 backorder_qty(sku)：可用量低于 BACKORDER_MIN 时返回差额，"
                "否则返回 0（阈值从 terms 模块导入）。"
            ),
            "tests": (
                "import stock\n"
                "import terms\n\n\n"
                "def test_backorder_low():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 4)\n'
                '    assert stock.backorder_qty("a") == 6\n\n\n'
                "def test_backorder_none():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 50)\n'
                '    assert stock.backorder_qty("a") == 0\n\n\n'
                "def test_min_regression():\n"
                "    assert terms.BACKORDER_MIN == 10\n"
            ),
            "ops": [
                ("replace", "stock.py", _s7a_old, _s7a_new),
                ("replace", "stock.py", _s7b_old, _s7b_new),
            ],
            "expect_targets": {"stock.py"},
        },
        {
            "instruction": (
                "请修改 stock.py 中的 reserve：qty 小于等于 0 时应抛 ValueError"
                "（正数预留行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import stock\n\n\n"
                "def test_reserve_zero():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 5)\n'
                "    with pytest.raises(ValueError):\n"
                '        stock.reserve("a", 0)\n\n\n'
                "def test_reserve_negative():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 5)\n'
                "    with pytest.raises(ValueError):\n"
                '        stock.reserve("a", -2)\n\n\n'
                "def test_reserve_ok_regression():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 5)\n'
                '    assert stock.reserve("a", 2) is True\n'
                '    assert stock.available("a") == 3\n'
            ),
            "ops": [("replace", "stock.py", _s8_old, _s8_new)],
            "expect_targets": {"stock.py"},
        },
        {
            "instruction": (
                "stock.py 新增 low_stock()：返回所有 backorder_qty 大于 0 的 sku 列表，"
                "按 sku 升序。"
            ),
            "tests": (
                "import stock\n\n\n"
                "def test_low_stock():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 4)\n'
                '    stock.receive("b", 50)\n'
                '    stock.receive("c", 9)\n'
                '    assert stock.low_stock() == ["a", "c"]\n\n\n'
                "def test_low_stock_empty():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 50)\n'
                "    assert stock.low_stock() == []\n\n\n"
                "def test_backorder_regression():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 4)\n'
                '    assert stock.backorder_qty("a") == 6\n'
            ),
            "ops": [("replace", "stock.py", _s9_old, _s9_new)],
            "expect_targets": {"stock.py"},
        },
        {
            "instruction": (
                "请修改 terms.py 中的 BACKORDER_MIN：应从 10 改为 3，"
                "回补缺口计算随之更新。"
            ),
            "tests": (
                "import terms\n"
                "import stock\n"
                "import ship\n\n\n"
                "def test_min_revised():\n"
                "    assert terms.BACKORDER_MIN == 3\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 4)\n'
                '    assert stock.backorder_qty("a") == 0\n'
                '    stock.receive("b", 1)\n'
                '    assert stock.backorder_qty("b") == 2\n'
                '    assert stock.low_stock() == ["b"]\n\n\n'
                "def test_full_chain():\n"
                "    stock.ITEMS.clear()\n"
                '    stock.receive("a", 10)\n'
                '    assert stock.available("a") == 10\n'
                '    assert stock.reserve("a", 4) is True\n'
                '    assert ship.reservation_line("a", 20) == "short=a"\n'
                '    assert stock.release("a", 4) == 10\n'
                '    assert stock.backorder_qty("a") == 0\n'
            ),
            "ops": [("replace", "terms.py", "BACKORDER_MIN = 10\n", "BACKORDER_MIN = 3\n")],
            "expect_targets": {"terms.py"},
        },
    ],
    info_points=[
        {"id": "ip_receive_contract", "type": "interface",
         "value": "receive 累加用量；qty<=0 拒绝",
         "locator": "instruction:step1 + instruction:step2",
         "needed_by_steps": [1, 2, 10],
         "redundant_in_instruction": True},
        {"id": "ip_reserve_semantics", "type": "implementation",
         "value": "可用不足返回 False 且不扣减",
         "locator": "instruction:step3 + stock.py",
         "needed_by_steps": [3, 5, 10],
         "redundant_in_instruction": True},
        {"id": "ip_backorder_threshold", "type": "critical_data",
         "value": "BACKORDER_MIN：5→10（step6）→3（step10）",
         "locator": "instruction:step6 + instruction:step7 + instruction:step10",
         "needed_by_steps": [6, 7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_items_shape", "type": "history",
         "value": "ITEMS 为 {sku: qty} 字典",
         "locator": "stock.py after step1 + assistant history",
         "needed_by_steps": [3, 4, 7, 9],
         "redundant_in_instruction": False},
        {"id": "ip_release_undoes", "type": "history",
         "value": "release 把预留数量加回并返回新可用量",
         "locator": "stock.py after step4 + assistant history",
         "needed_by_steps": [4, 10],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：行列表目录（查行→唯一约束→改数→合计→挂单上限两次改约）

_cat_b = (
    '"""Catalog rows."""\n\n\n'
    "ROWS = []\n\n\n"
    "def add_row(sku, qty):\n"
    '    ROWS.append({"sku": sku, "qty": qty})\n'
)
_cap_b = (
    '"""Capacity caps."""\n\n\n'
    "MAX_HOLD = 4\n"
)
_frt_b = (
    '"""Front desk."""\n\n\n'
    "def greeting():\n"
    '    return "welcome"\n'
)
_c1_old = 'def add_row(sku, qty):\n    ROWS.append({"sku": sku, "qty": qty})'
_c1_new = _c1_old + (
    "\n\n\ndef find(sku):\n"
    "    for row in ROWS:\n"
    '        if row["sku"] == sku:\n'
    "            return row\n"
    "    return None"
)
_c2_old = _c1_old
_c2_new = (
    "def add_row(sku, qty):\n"
    "    if find(sku) is not None:\n"
    '        raise ValueError("sku")\n'
    '    ROWS.append({"sku": sku, "qty": qty})'
)
_c3_old = (
    "def find(sku):\n"
    "    for row in ROWS:\n"
    '        if row["sku"] == sku:\n'
    "            return row\n"
    "    return None"
)
_c3_new = _c3_old + (
    "\n\n\ndef set_qty(sku, qty):\n"
    "    row = find(sku)\n"
    "    if row is None:\n"
    "        return False\n"
    '    row["qty"] = qty\n'
    "    return True"
)
_c4_old = (
    "def set_qty(sku, qty):\n"
    "    row = find(sku)\n"
    "    if row is None:\n"
    "        return False\n"
    '    row["qty"] = qty\n'
    "    return True"
)
_c4_new = _c4_old + "\n\n\ndef total():\n    return sum(row[\"qty\"] for row in ROWS)"
_c5a_old = '"""Front desk."""'
_c5a_new = '"""Front desk."""\nfrom catalog import find'
_c5b_old = 'def greeting():\n    return "welcome"'
_c5b_new = _c5b_old + (
    "\n\n\ndef stock_line(sku):\n"
    "    row = find(sku)\n"
    "    if row is None:\n"
    '        return f"sku={sku} qty=missing"\n'
    '    return f"sku={sku} qty={row[\'qty\']}"'
)
_c7a_old = '"""Catalog rows."""'
_c7a_new = '"""Catalog rows."""\nfrom caps import MAX_HOLD'
_c7b_old = 'def total():\n    return sum(row["qty"] for row in ROWS)'
_c7b_new = _c7b_old + (
    "\n\n\ndef hold(sku, n):\n"
    "    if n > MAX_HOLD:\n"
    '        raise ValueError("n")\n'
    "    row = find(sku)\n"
    "    if row is None:\n"
    "        raise KeyError(sku)\n"
    '    row["qty"] = row["qty"] - n\n'
    '    return row["qty"]'
)
_c8_old = (
    "def hold(sku, n):\n"
    "    if n > MAX_HOLD:\n"
    '        raise ValueError("n")\n'
    "    row = find(sku)\n"
    "    if row is None:\n"
    "        raise KeyError(sku)\n"
    '    row["qty"] = row["qty"] - n\n'
    '    return row["qty"]'
)
_c8_new = (
    "def hold(sku, n):\n"
    "    if n <= 0:\n"
    '        raise ValueError("n")\n'
    "    if n > MAX_HOLD:\n"
    '        raise ValueError("n")\n'
    "    row = find(sku)\n"
    "    if row is None:\n"
    "        raise KeyError(sku)\n"
    '    row["qty"] = row["qty"] - n\n'
    '    return row["qty"]'
)
_c9_old = _c8_new
_c9_new = _c8_new + (
    "\n\n\ndef low_rows(k):\n"
    '    return sorted(row["sku"] for row in ROWS if row["qty"] < k)'
)
T(
    id="ind_L03b",
    family="ind_long_warehouse",
    type="inventory_reservation_evolution",
    difficulty="long",
    focus="10 步行式目录演进：查行→唯一约束→改数→合计→前台消费方→挂单上限两次改约",
    files={"catalog.py": _cat_b, "caps.py": _cap_b, "front.py": _frt_b},
    steps=[
        {
            "instruction": (
                "catalog.py 新增 find(sku)：返回首个 sku 匹配的行（没有则返回 None）。"
            ),
            "tests": (
                "import catalog\n\n\n"
                "def test_find():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                '    catalog.add_row("b", 7)\n'
                '    row = catalog.find("b")\n'
                '    assert row["qty"] == 7\n\n\n'
                "def test_find_missing():\n"
                "    catalog.ROWS.clear()\n"
                '    assert catalog.find("zz") is None\n\n\n'
                "def test_add_regression():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 1)\n'
                '    assert catalog.ROWS == [{"sku": "a", "qty": 1}]\n'
            ),
            "ops": [("replace", "catalog.py", _c1_old, _c1_new)],
            "expect_targets": {"catalog.py"},
        },
        {
            "instruction": (
                "请修改 catalog.py 中的 add_row：sku 已存在时抛 ValueError"
                "（新增其他 sku 行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import catalog\n\n\n"
                "def test_duplicate_rejected():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                "    with pytest.raises(ValueError):\n"
                '        catalog.add_row("a", 9)\n'
                '    assert catalog.find("a")["qty"] == 5\n\n\n'
                "def test_new_sku_ok():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                '    catalog.add_row("b", 6)\n'
                "    assert len(catalog.ROWS) == 2\n"
            ),
            "ops": [("replace", "catalog.py", _c2_old, _c2_new)],
            "expect_targets": {"catalog.py"},
        },
        {
            "instruction": (
                "catalog.py 新增 set_qty(sku, qty)：把匹配行的数量改为 qty 并返回 True；"
                "没有该行返回 False。"
            ),
            "tests": (
                "import catalog\n\n\n"
                "def test_set_qty():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                '    assert catalog.set_qty("a", 12) is True\n'
                '    assert catalog.find("a")["qty"] == 12\n\n\n'
                "def test_set_qty_missing():\n"
                "    catalog.ROWS.clear()\n"
                '    assert catalog.set_qty("zz", 1) is False\n\n\n'
                "def test_duplicate_regression():\n"
                "    import pytest\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                "    with pytest.raises(ValueError):\n"
                '        catalog.add_row("a", 9)\n'
            ),
            "ops": [("replace", "catalog.py", _c3_old, _c3_new)],
            "expect_targets": {"catalog.py"},
        },
        {
            "instruction": (
                "catalog.py 新增 total()：返回所有行数量之和（空表返回 0）。"
            ),
            "tests": (
                "import catalog\n\n\n"
                "def test_total():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                '    catalog.add_row("b", 7)\n'
                "    assert catalog.total() == 12\n\n\n"
                "def test_total_empty():\n"
                "    catalog.ROWS.clear()\n"
                "    assert catalog.total() == 0\n\n\n"
                "def test_set_qty_regression():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                '    assert catalog.set_qty("a", 3) is True\n'
                "    assert catalog.total() == 3\n"
            ),
            "ops": [("replace", "catalog.py", _c4_old, _c4_new)],
            "expect_targets": {"catalog.py"},
        },
        {
            "instruction": (
                "front.py 新增 stock_line(sku)：调用 catalog.py 的 find 取行，"
                "有行输出 'sku=x qty=y'，无行输出 'sku=x qty=missing'"
                "（需要补充 import）。"
            ),
            "tests": (
                "import front\n"
                "import catalog\n\n\n"
                "def test_stock_line():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                '    assert front.stock_line("a") == "sku=a qty=5"\n\n\n'
                "def test_stock_line_missing():\n"
                "    catalog.ROWS.clear()\n"
                '    assert front.stock_line("zz") == "sku=zz qty=missing"\n\n\n'
                "def test_greeting_regression():\n"
                '    assert front.greeting() == "welcome"\n\n\n'
                "def test_total_regression():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                "    assert catalog.total() == 5\n"
            ),
            "ops": [
                ("replace", "front.py", _c5a_old, _c5a_new),
                ("replace", "front.py", _c5b_old, _c5b_new),
            ],
            "expect_targets": {"front.py", "catalog.py"},
        },
        {
            "instruction": (
                "请修改 caps.py 中的 MAX_HOLD：应从 4 改为 6。"
            ),
            "tests": (
                "import caps\n"
                "import front\n"
                "import catalog\n\n\n"
                "def test_cap_updated():\n"
                "    assert caps.MAX_HOLD == 6\n\n\n"
                "def test_stock_line_regression():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                '    assert front.stock_line("a") == "sku=a qty=5"\n'
            ),
            "ops": [("replace", "caps.py", "MAX_HOLD = 4\n", "MAX_HOLD = 6\n")],
            "expect_targets": {"caps.py"},
        },
        {
            "instruction": (
                "catalog.py 新增 hold(sku, n)：行不存在抛 KeyError；"
                "n 超过 caps 模块的 MAX_HOLD 抛 ValueError；"
                "否则扣减数量并返回新数量。"
            ),
            "tests": (
                "import pytest\n"
                "import catalog\n\n\n"
                "def test_hold_ok():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 10)\n'
                '    assert catalog.hold("a", 3) == 7\n'
                '    assert catalog.find("a")["qty"] == 7\n\n\n'
                "def test_hold_over_cap():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 10)\n'
                "    with pytest.raises(ValueError):\n"
                '        catalog.hold("a", 7)\n\n\n'
                "def test_hold_missing_row():\n"
                "    catalog.ROWS.clear()\n"
                "    with pytest.raises(KeyError):\n"
                '        catalog.hold("zz", 1)\n\n\n'
                "def test_total_regression():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 5)\n'
                "    assert catalog.total() == 5\n"
            ),
            "ops": [
                ("replace", "catalog.py", _c7a_old, _c7a_new),
                ("replace", "catalog.py", _c7b_old, _c7b_new),
            ],
            "expect_targets": {"catalog.py"},
        },
        {
            "instruction": (
                "请修改 catalog.py 中的 hold：n 小于等于 0 时也应抛 ValueError"
                "（正数上限规则不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import catalog\n\n\n"
                "def test_hold_zero():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 10)\n'
                "    with pytest.raises(ValueError):\n"
                '        catalog.hold("a", 0)\n\n\n'
                "def test_hold_negative():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 10)\n'
                "    with pytest.raises(ValueError):\n"
                '        catalog.hold("a", -1)\n\n\n'
                "def test_hold_ok_regression():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 10)\n'
                '    assert catalog.hold("a", 3) == 7\n'
            ),
            "ops": [("replace", "catalog.py", _c8_old, _c8_new)],
            "expect_targets": {"catalog.py"},
        },
        {
            "instruction": (
                "catalog.py 新增 low_rows(k)：返回数量小于 k 的 sku 列表，按 sku 升序。"
            ),
            "tests": (
                "import catalog\n\n\n"
                "def test_low_rows():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("c", 2)\n'
                '    catalog.add_row("a", 9)\n'
                '    catalog.add_row("b", 4)\n'
                '    assert catalog.low_rows(5) == ["b", "c"]\n\n\n'
                "def test_low_rows_empty():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 9)\n'
                "    assert catalog.low_rows(5) == []\n\n\n"
                "def test_hold_regression():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 10)\n'
                '    assert catalog.hold("a", 3) == 7\n'
            ),
            "ops": [("replace", "catalog.py", _c9_old, _c9_new)],
            "expect_targets": {"catalog.py"},
        },
        {
            "instruction": (
                "请修改 caps.py 中的 MAX_HOLD：应从 6 改为 2，"
                "单次挂单上限随之收紧。"
            ),
            "tests": (
                "import pytest\n"
                "import caps\n"
                "import catalog\n"
                "import front\n\n\n"
                "def test_cap_revised():\n"
                "    assert caps.MAX_HOLD == 2\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 10)\n'
                "    with pytest.raises(ValueError):\n"
                '        catalog.hold("a", 3)\n\n\n'
                "def test_full_chain():\n"
                "    catalog.ROWS.clear()\n"
                '    catalog.add_row("a", 10)\n'
                '    catalog.add_row("b", 1)\n'
                '    assert catalog.find("a")["qty"] == 10\n'
                "    assert catalog.total() == 11\n"
                '    assert catalog.hold("a", 2) == 8\n'
                '    assert front.stock_line("a") == "sku=a qty=8"\n'
                '    assert catalog.low_rows(5) == ["b"]\n'
            ),
            "ops": [("replace", "caps.py", "MAX_HOLD = 6\n", "MAX_HOLD = 2\n")],
            "expect_targets": {"caps.py"},
        },
    ],
    info_points=[
        {"id": "ip_find_row", "type": "implementation",
         "value": "find 返回首个 sku 匹配行，缺失返回 None",
         "locator": "instruction:step1 + catalog.py",
         "needed_by_steps": [1, 3, 5, 7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_unique_sku", "type": "interface",
         "value": "add_row 拒绝重复 sku",
         "locator": "instruction:step2 + catalog.py",
         "needed_by_steps": [2, 3],
         "redundant_in_instruction": True},
        {"id": "ip_hold_rules", "type": "implementation",
         "value": "hold：缺行 KeyError、超上限 ValueError、扣减返回新值；n<=0 拒绝",
         "locator": "instruction:step7 + instruction:step8",
         "needed_by_steps": [7, 8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_max_hold_values", "type": "critical_data",
         "value": "MAX_HOLD：4→6（step6）→2（step10）",
         "locator": "instruction:step6 + instruction:step10",
         "needed_by_steps": [6, 7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_rows_shape", "type": "history",
         "value": "ROWS 为含 sku/qty 键的字典行列表",
         "locator": "catalog.py after step1 + assistant history",
         "needed_by_steps": [3, 4, 9],
         "redundant_in_instruction": False},
        {"id": "ip_hold_cap_coupling", "type": "history",
         "value": "hold 读取 caps.MAX_HOLD（step7 引入，step10 改约自动生效）",
         "locator": "catalog.py after step7 + assistant history",
         "needed_by_steps": [7, 10],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ LF4 ind_long_undo
# 变体 a：行文档命令日志（应用→历史查询→回滚→重做→压缩语义改约）

_doc_a = (
    '"""Line document."""\n\n\n'
    'LINES = ["alpha", "beta"]\n\n\n'
    "def append_line(text):\n"
    "    LINES.append(text)\n"
)
_jrn_a = (
    '"""Command journal."""\n\n\n'
    "JOURNAL = []\n\n\n"
    "def record(entry):\n"
    "    JOURNAL.append(entry)\n"
)
_vew_a = (
    '"""Viewer."""\n\n\n'
    "def title():\n"
    '    return "doc-view"\n'
)
_a1_old = "def append_line(text):\n    LINES.append(text)"
_a1_new = _a1_old + (
    "\n\n\ndef remove_last():\n"
    "    if not LINES:\n"
    "        return None\n"
    "    return LINES.pop()"
)
_a2_old = "def record(entry):\n    JOURNAL.append(entry)"
_a2_new = _a2_old + "\n\n\ndef size():\n    return len(JOURNAL)"
_a3a_old = '"""Line document."""'
_a3a_new = '"""Line document."""\nfrom journal import record'
_a3b_old = "def append_line(text):\n    LINES.append(text)"
_a3b_new = (
    "def append_line(text):\n"
    "    LINES.append(text)\n"
    '    record(("append", text))'
)
_a4a_old = '"""Viewer."""'
_a4a_new = '"""Viewer."""\nfrom doc import LINES'
_a4b_old = 'def title():\n    return "doc-view"'
_a4b_new = _a4b_old + (
    "\n\n\ndef last_line():\n"
    "    if not LINES:\n"
    "        return None\n"
    "    return LINES[-1]"
)
_a5_old = "def size():\n    return len(JOURNAL)"
_a5_new = _a5_old + (
    "\n\n\ndef history(kind=None):\n"
    "    if kind is None:\n"
    "        return list(JOURNAL)\n"
    "    return [e for e in JOURNAL if e[0] == kind]"
)
_a6a_old = 'LINES = ["alpha", "beta"]'
_a6a_new = 'LINES = ["alpha", "beta"]\nREDO_STACK = []'
_a6b_old = "from journal import record"
_a6b_new = "from journal import record, JOURNAL"
_a6c_old = (
    "def remove_last():\n"
    "    if not LINES:\n"
    "        return None\n"
    "    return LINES.pop()"
)
_a6c_new = _a6c_old + (
    "\n\n\ndef undo_last():\n"
    "    if not LINES or not JOURNAL or JOURNAL[-1][0] != \"append\":\n"
    "        return None\n"
    "    kind, text = JOURNAL.pop()\n"
    "    REDO_STACK.append(text)\n"
    "    return LINES.pop()"
)
_a7_old = (
    "def undo_last():\n"
    "    if not LINES or not JOURNAL or JOURNAL[-1][0] != \"append\":\n"
    "        return None\n"
    "    kind, text = JOURNAL.pop()\n"
    "    REDO_STACK.append(text)\n"
    "    return LINES.pop()"
)
_a7_new = _a7_old + (
    "\n\n\ndef redo_last():\n"
    "    if not REDO_STACK:\n"
    "        return None\n"
    "    text = REDO_STACK.pop()\n"
    "    LINES.append(text)\n"
    '    record(("append", text))\n'
    "    return text"
)
_a8_old = (
    "def history(kind=None):\n"
    "    if kind is None:\n"
    "        return list(JOURNAL)\n"
    "    return [e for e in JOURNAL if e[0] == kind]"
)
_a8_new = _a8_old + (
    "\n\n\ndef compact():\n"
    "    if not JOURNAL:\n"
    "        return None\n"
    "    keep = JOURNAL[-1]\n"
    "    JOURNAL[:] = [keep]\n"
    "    return keep"
)
_a9_old = (
    "def compact():\n"
    "    if not JOURNAL:\n"
    "        return None\n"
    "    keep = JOURNAL[-1]\n"
    "    JOURNAL[:] = [keep]\n"
    "    return keep"
)
_a9_new = (
    "def compact():\n"
    "    if not JOURNAL:\n"
    "        return None\n"
    "    keep = JOURNAL[-3:]\n"
    "    JOURNAL[:] = keep\n"
    "    return keep[-1]"
)
_a10_old = (
    "def append_line(text):\n"
    "    LINES.append(text)\n"
    '    record(("append", text))'
)
_a10_new = (
    "def append_line(text):\n"
    "    if not text or not text.strip():\n"
    '        raise ValueError("text")\n'
    "    LINES.append(text)\n"
    '    record(("append", text))'
)
T(
    id="ind_L04a",
    family="ind_long_undo",
    type="command_log_evolution",
    difficulty="long",
    focus="10 步命令日志演进：应用→历史查询→回滚→重做→压缩引入→压缩语义改约→边界",
    files={"doc.py": _doc_a, "journal.py": _jrn_a, "viewer.py": _vew_a},
    steps=[
        {
            "instruction": (
                "doc.py 新增 remove_last()：删除并返回最后一行；空文档返回 None。"
            ),
            "tests": (
                "import doc\n\n\n"
                "def test_remove_last():\n"
                "    doc.LINES.clear()\n"
                '    doc.LINES.extend(["a", "b"])\n'
                '    assert doc.remove_last() == "b"\n'
                '    assert doc.LINES == ["a"]\n\n\n'
                "def test_remove_empty():\n"
                "    doc.LINES.clear()\n"
                "    assert doc.remove_last() is None\n\n\n"
                "def test_append_regression():\n"
                "    doc.LINES.clear()\n"
                '    doc.append_line("x")\n'
                '    assert doc.LINES == ["x"]\n'
            ),
            "ops": [("replace", "doc.py", _a1_old, _a1_new)],
            "expect_targets": {"doc.py"},
        },
        {
            "instruction": (
                "journal.py 新增 size()：返回 JOURNAL 中的条目数（空日志返回 0）。"
            ),
            "tests": (
                "import journal\n\n\n"
                "def test_size_empty():\n"
                "    journal.JOURNAL.clear()\n"
                "    assert journal.size() == 0\n\n\n"
                "def test_size_after_record():\n"
                "    journal.JOURNAL.clear()\n"
                '    journal.record(("append", "a"))\n'
                '    journal.record(("append", "b"))\n'
                "    assert journal.size() == 2\n\n\n"
                "def test_record_regression():\n"
                "    journal.JOURNAL.clear()\n"
                '    journal.record(("append", "a"))\n'
                '    assert journal.JOURNAL == [("append", "a")]\n'
            ),
            "ops": [("replace", "journal.py", _a2_old, _a2_new)],
            "expect_targets": {"journal.py"},
        },
        {
            "instruction": (
                "请修改 doc.py 中的 append_line：追加行的同时把 ('append', text) "
                "记入 journal.py 的 JOURNAL（需要补充 import）。"
            ),
            "tests": (
                "import doc\n"
                "import journal\n\n\n"
                "def test_append_records():\n"
                "    doc.LINES.clear()\n"
                "    journal.JOURNAL.clear()\n"
                '    doc.append_line("hello")\n'
                '    assert doc.LINES == ["hello"]\n'
                '    assert journal.JOURNAL == [("append", "hello")]\n\n\n'
                "def test_append_multiple():\n"
                "    doc.LINES.clear()\n"
                "    journal.JOURNAL.clear()\n"
                '    doc.append_line("a")\n'
                '    doc.append_line("b")\n'
                "    assert journal.size() == 2\n\n\n"
                "def test_remove_regression():\n"
                "    doc.LINES.clear()\n"
                '    doc.LINES.extend(["a", "b"])\n'
                '    assert doc.remove_last() == "b"\n'
            ),
            "ops": [
                ("replace", "doc.py", _a3a_old, _a3a_new),
                ("replace", "doc.py", _a3b_old, _a3b_new),
            ],
            "expect_targets": {"doc.py", "journal.py"},
        },
        {
            "instruction": (
                "viewer.py 新增 last_line()：返回 doc.py 的 LINES 最后一行，"
                "空文档返回 None（需要补充 import）。"
            ),
            "tests": (
                "import doc\n"
                "import viewer\n\n\n"
                "def test_last_line():\n"
                "    doc.LINES.clear()\n"
                '    doc.LINES.extend(["a", "b"])\n'
                '    assert viewer.last_line() == "b"\n\n\n'
                "def test_last_line_empty():\n"
                "    doc.LINES.clear()\n"
                "    assert viewer.last_line() is None\n\n\n"
                "def test_title_regression():\n"
                '    assert viewer.title() == "doc-view"\n\n\n'
                "def test_append_records_regression():\n"
                "    doc.LINES.clear()\n"
                "    import journal\n"
                "    journal.JOURNAL.clear()\n"
                '    doc.append_line("z")\n'
                '    assert journal.JOURNAL == [("append", "z")]\n'
            ),
            "ops": [
                ("replace", "viewer.py", _a4a_old, _a4a_new),
                ("replace", "viewer.py", _a4b_old, _a4b_new),
            ],
            "expect_targets": {"viewer.py", "doc.py"},
        },
        {
            "instruction": (
                "journal.py 新增 history(kind=None)：返回匹配 kind 的条目列表，"
                "kind 为 None 时返回全部条目。"
            ),
            "tests": (
                "import journal\n\n\n"
                "def test_history_all():\n"
                "    journal.JOURNAL.clear()\n"
                '    journal.record(("append", "a"))\n'
                '    journal.record(("undo", "a"))\n'
                '    assert journal.history() == [("append", "a"), ("undo", "a")]\n\n\n'
                "def test_history_kind():\n"
                "    journal.JOURNAL.clear()\n"
                '    journal.record(("append", "a"))\n'
                '    journal.record(("undo", "a"))\n'
                '    assert journal.history("undo") == [("undo", "a")]\n\n\n'
                "def test_size_regression():\n"
                "    journal.JOURNAL.clear()\n"
                '    journal.record(("append", "a"))\n'
                "    assert journal.size() == 1\n"
            ),
            "ops": [("replace", "journal.py", _a5_old, _a5_new)],
            "expect_targets": {"journal.py"},
        },
        {
            "instruction": (
                "doc.py 新增 undo_last()：撤销最近一条 append（移除文档最后一行、"
                "弹出该日志条目并压入 REDO_STACK），无可撤销时返回 None"
                "（需要补充 journal.py 的 JOURNAL）。"
            ),
            "tests": (
                "import doc\n"
                "import journal\n\n\n"
                "def test_undo_last():\n"
                "    doc.LINES.clear()\n"
                "    journal.JOURNAL.clear()\n"
                '    doc.append_line("a")\n'
                '    doc.append_line("b")\n'
                '    assert doc.undo_last() == "b"\n'
                '    assert doc.LINES == ["a"]\n'
                '    assert journal.JOURNAL == [("append", "a")]\n'
                '    assert doc.REDO_STACK == ["b"]\n\n\n'
                "def test_undo_nothing():\n"
                "    doc.LINES.clear()\n"
                "    journal.JOURNAL.clear()\n"
                "    assert doc.undo_last() is None\n\n\n"
                "def test_last_line_regression():\n"
                "    doc.LINES.clear()\n"
                '    doc.LINES.extend(["x", "y"])\n'
                "    import viewer\n"
                '    assert viewer.last_line() == "y"\n'
            ),
            "ops": [
                ("replace", "doc.py", _a6a_old, _a6a_new),
                ("replace", "doc.py", _a6b_old, _a6b_new),
                ("replace", "doc.py", _a6c_old, _a6c_new),
            ],
            "expect_targets": {"doc.py", "journal.py"},
        },
        {
            "instruction": (
                "doc.py 新增 redo_last()：从 REDO_STACK 弹出文本重新追加为一行并记日志，"
                "栈空返回 None。"
            ),
            "tests": (
                "import doc\n"
                "import journal\n\n\n"
                "def test_redo():\n"
                "    doc.LINES.clear()\n"
                "    journal.JOURNAL.clear()\n"
                '    doc.append_line("a")\n'
                "    doc.undo_last()\n"
                '    assert doc.redo_last() == "a"\n'
                '    assert doc.LINES == ["a"]\n'
                '    assert journal.JOURNAL == [("append", "a")]\n'
                "    assert doc.REDO_STACK == []\n\n\n"
                "def test_redo_empty():\n"
                "    doc.LINES.clear()\n"
                "    journal.JOURNAL.clear()\n"
                "    assert doc.redo_last() is None\n\n\n"
                "def test_undo_regression():\n"
                "    doc.LINES.clear()\n"
                "    journal.JOURNAL.clear()\n"
                '    doc.append_line("a")\n'
                '    doc.append_line("b")\n'
                '    assert doc.undo_last() == "b"\n'
                '    assert doc.LINES == ["a"]\n'
            ),
            "ops": [("replace", "doc.py", _a7_old, _a7_new)],
            "expect_targets": {"doc.py"},
        },
        {
            "instruction": (
                "journal.py 新增 compact()：压缩日志只保留最后一条 entry，"
                "返回保留的条目；空日志返回 None。"
            ),
            "tests": (
                "import journal\n\n\n"
                "def test_compact():\n"
                "    journal.JOURNAL.clear()\n"
                '    journal.record(("append", "a"))\n'
                '    journal.record(("append", "b"))\n'
                '    journal.record(("undo", "b"))\n'
                "    kept = journal.compact()\n"
                '    assert kept == ("undo", "b")\n'
                '    assert journal.JOURNAL == [("undo", "b")]\n\n\n'
                "def test_compact_empty():\n"
                "    journal.JOURNAL.clear()\n"
                "    assert journal.compact() is None\n\n\n"
                "def test_history_regression():\n"
                "    journal.JOURNAL.clear()\n"
                '    journal.record(("append", "a"))\n'
                '    assert journal.history("append") == [("append", "a")]\n'
            ),
            "ops": [("replace", "journal.py", _a8_old, _a8_new)],
            "expect_targets": {"journal.py"},
        },
        {
            "instruction": (
                "请修改 journal.py 中的 compact：压缩后应保留最近 3 条"
                "（当前只保留最后 1 条），返回值仍为最后一条。"
            ),
            "tests": (
                "import journal\n\n\n"
                "def test_compact_keeps_three():\n"
                "    journal.JOURNAL.clear()\n"
                "    for i in range(5):\n"
                '        journal.record(("append", f"l{i}"))\n'
                "    kept = journal.compact()\n"
                '    assert kept == ("append", "l4")\n'
                '    assert journal.JOURNAL == [\n'
                '        ("append", "l2"), ("append", "l3"), ("append", "l4")\n'
                "    ]\n\n\n"
                "def test_compact_under_three():\n"
                "    journal.JOURNAL.clear()\n"
                '    journal.record(("append", "a"))\n'
                '    journal.record(("append", "b"))\n'
                "    journal.compact()\n"
                "    assert len(journal.JOURNAL) == 2\n\n\n"
                "def test_compact_empty_regression():\n"
                "    journal.JOURNAL.clear()\n"
                "    assert journal.compact() is None\n"
            ),
            "ops": [("replace", "journal.py", _a9_old, _a9_new)],
            "expect_targets": {"journal.py"},
        },
        {
            "instruction": (
                "请修改 doc.py 中的 append_line：text 为空白时抛 ValueError"
                "（非空追加行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import doc\n"
                "import journal\n\n\n"
                "def test_append_blank():\n"
                "    doc.LINES.clear()\n"
                "    journal.JOURNAL.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        doc.append_line("")\n'
                "    with pytest.raises(ValueError):\n"
                '        doc.append_line("   ")\n\n\n'
                "def test_append_ok():\n"
                "    doc.LINES.clear()\n"
                "    journal.JOURNAL.clear()\n"
                '    doc.append_line("ok")\n'
                '    assert doc.LINES == ["ok"]\n'
                '    assert journal.JOURNAL == [("append", "ok")]\n\n\n'
                "def test_compact_regression():\n"
                "    journal.JOURNAL.clear()\n"
                "    for i in range(4):\n"
                '        journal.record(("append", f"l{i}"))\n'
                "    journal.compact()\n"
                "    assert len(journal.JOURNAL) == 3\n"
            ),
            "ops": [("replace", "doc.py", _a10_old, _a10_new)],
            "expect_targets": {"doc.py"},
        },
    ],
    info_points=[
        {"id": "ip_remove_last", "type": "interface",
         "value": "remove_last 删除并返回末行，空文档返回 None",
         "locator": "instruction:step1 + doc.py",
         "needed_by_steps": [1, 6],
         "redundant_in_instruction": True},
        {"id": "ip_append_records", "type": "implementation",
         "value": "append_line 记 ('append', text) 到 JOURNAL",
         "locator": "instruction:step3 + doc.py",
         "needed_by_steps": [3, 6, 7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_undo_redo", "type": "implementation",
         "value": "undo 弹日志并压 REDO_STACK；redo 弹栈重追加",
         "locator": "instruction:step6 + instruction:step7",
         "needed_by_steps": [6, 7],
         "redundant_in_instruction": True},
        {"id": "ip_journal_shape", "type": "history",
         "value": "JOURNAL 为 (kind, text) 元组列表",
         "locator": "journal.py after step2 + assistant history",
         "needed_by_steps": [5, 6, 8, 9],
         "redundant_in_instruction": False},
        {"id": "ip_compact_keep3", "type": "critical_data",
         "value": "compact 保留条数 1（step8）→3（step9 改约）",
         "locator": "instruction:step8 + instruction:step9",
         "needed_by_steps": [8, 9, 10],
         "redundant_in_instruction": True},
    ],
)

# 变体 b：计数器反向撤销（应用→历史查询→回滚→重做→压缩改约）

_cnt_b = (
    '"""Counter state."""\n\n\n'
    "VALUE = 0\n\n\n"
    "def bump(delta):\n"
    "    global VALUE\n"
    "    VALUE += delta\n"
    "    return VALUE\n"
)
_ops_b = (
    '"""Op log."""\n\n\n'
    "OPS = []\n\n\n"
    "def push(op):\n"
    "    OPS.append(op)\n"
)
_rpt_b = (
    '"""Report."""\n\n\n'
    "def banner():\n"
    '    return "counter-report"\n'
)
_b1_old = (
    "def bump(delta):\n"
    "    global VALUE\n"
    "    VALUE += delta\n"
    "    return VALUE"
)
_b1_new = _b1_old + "\n\n\ndef get():\n    return VALUE"
_b2_old = "def push(op):\n    OPS.append(op)"
_b2_new = _b2_old + "\n\n\ndef length():\n    return len(OPS)"
_b3a_old = '"""Counter state."""'
_b3a_new = '"""Counter state."""\nfrom ops_log import push'
_b3b_old = (
    "def bump(delta):\n"
    "    global VALUE\n"
    "    VALUE += delta\n"
    "    return VALUE"
)
_b3b_new = (
    "def bump(delta):\n"
    "    global VALUE\n"
    "    VALUE += delta\n"
    '    push({"op": "bump", "delta": delta})\n'
    "    return VALUE"
)
_b4a_old = '"""Report."""'
_b4a_new = '"""Report."""\nimport counter'
_b4b_old = 'def banner():\n    return "counter-report"'
_b4b_new = _b4b_old + '\n\n\ndef status():\n    return f"value={counter.VALUE}"'
_b5_old = "def length():\n    return len(OPS)"
_b5_new = _b5_old + (
    "\n\n\ndef last_op():\n"
    "    if not OPS:\n"
    "        return None\n"
    "    return OPS[-1]"
)
_b6a_old = "OPS = []"
_b6a_new = "OPS = []\nUNDONE = []"
_b6b_old = "from ops_log import push"
_b6b_new = "from ops_log import push, OPS, UNDONE"
_b6c_old = "def get():\n    return VALUE"
_b6c_new = _b6c_old + (
    "\n\n\ndef undo_last():\n"
    "    global VALUE\n"
    "    if not OPS:\n"
    "        return None\n"
    "    op = OPS.pop()\n"
    '    if op["op"] == "bump":\n'
    "        VALUE -= op[\"delta\"]\n"
    "    UNDONE.append(op)\n"
    "    return op"
)
_b7_old = (
    "def undo_last():\n"
    "    global VALUE\n"
    "    if not OPS:\n"
    "        return None\n"
    "    op = OPS.pop()\n"
    '    if op["op"] == "bump":\n'
    "        VALUE -= op[\"delta\"]\n"
    "    UNDONE.append(op)\n"
    "    return op"
)
_b7_new = _b7_old + (
    "\n\n\ndef redo_last():\n"
    "    if not UNDONE:\n"
    "        return None\n"
    "    op = UNDONE.pop()\n"
    "    return bump(op[\"delta\"])"
)
_b8_old = (
    "def last_op():\n"
    "    if not OPS:\n"
    "        return None\n"
    "    return OPS[-1]"
)
_b8_new = _b8_old + (
    "\n\n\ndef compact():\n"
    "    n = len(OPS)\n"
    "    OPS.clear()\n"
    "    return n"
)
_b9_old = (
    "def compact():\n"
    "    n = len(OPS)\n"
    "    OPS.clear()\n"
    "    return n"
)
_b9_new = (
    "def compact():\n"
    "    n = len(OPS)\n"
    "    del OPS[:-2]\n"
    "    return n"
)
_b10_old = (
    "def bump(delta):\n"
    "    global VALUE\n"
    "    VALUE += delta\n"
    '    push({"op": "bump", "delta": delta})\n'
    "    return VALUE"
)
_b10_new = (
    "def bump(delta):\n"
    "    if delta == 0:\n"
    '        raise ValueError("delta")\n'
    "    global VALUE\n"
    "    VALUE += delta\n"
    '    push({"op": "bump", "delta": delta})\n'
    "    return VALUE"
)
T(
    id="ind_L04b",
    family="ind_long_undo",
    type="command_log_evolution",
    difficulty="long",
    focus="10 步反向撤销演进：应用→历史查询→回滚→重做→压缩引入→压缩改约→零步拒绝",
    files={"counter.py": _cnt_b, "ops_log.py": _ops_b, "report.py": _rpt_b},
    steps=[
        {
            "instruction": "counter.py 新增 get()：返回当前 VALUE。",
            "tests": (
                "import counter\n\n\n"
                "def test_get():\n"
                "    counter.VALUE = 5\n"
                "    assert counter.get() == 5\n\n\n"
                "def test_bump_regression():\n"
                "    counter.VALUE = 0\n"
                "    counter.bump(3)\n"
                "    assert counter.VALUE == 3\n"
            ),
            "ops": [("replace", "counter.py", _b1_old, _b1_new)],
            "expect_targets": {"counter.py"},
        },
        {
            "instruction": (
                "ops_log.py 新增 length()：返回 OPS 中的条目数（空日志返回 0）。"
            ),
            "tests": (
                "import ops_log\n\n\n"
                "def test_length_empty():\n"
                "    ops_log.OPS.clear()\n"
                "    assert ops_log.length() == 0\n\n\n"
                "def test_length_after_push():\n"
                "    ops_log.OPS.clear()\n"
                '    ops_log.push({"op": "bump", "delta": 1})\n'
                '    ops_log.push({"op": "bump", "delta": 2})\n'
                "    assert ops_log.length() == 2\n\n\n"
                "def test_push_regression():\n"
                "    ops_log.OPS.clear()\n"
                '    ops_log.push({"op": "bump", "delta": 1})\n'
                '    assert ops_log.OPS == [{"op": "bump", "delta": 1}]\n'
            ),
            "ops": [("replace", "ops_log.py", _b2_old, _b2_new)],
            "expect_targets": {"ops_log.py"},
        },
        {
            "instruction": (
                "请修改 counter.py 中的 bump：每次自增后把 "
                "{'op': 'bump', 'delta': delta} 记入 ops_log.py 的 OPS"
                "（需要补充 import）。"
            ),
            "tests": (
                "import counter\n"
                "import ops_log\n\n\n"
                "def test_bump_records():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    counter.bump(4)\n"
                "    assert counter.VALUE == 4\n"
                '    assert ops_log.OPS == [{"op": "bump", "delta": 4}]\n\n\n'
                "def test_bump_twice_records():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    counter.bump(1)\n"
                "    counter.bump(2)\n"
                "    assert ops_log.length() == 2\n"
                "    assert counter.VALUE == 3\n\n\n"
                "def test_get_regression():\n"
                "    counter.VALUE = 7\n"
                "    assert counter.get() == 7\n"
            ),
            "ops": [
                ("replace", "counter.py", _b3a_old, _b3a_new),
                ("replace", "counter.py", _b3b_old, _b3b_new),
            ],
            "expect_targets": {"counter.py", "ops_log.py"},
        },
        {
            "instruction": (
                "report.py 新增 status()：返回当前计数值，格式为 'value=N'"
                "（需要补充 import）。"
            ),
            "tests": (
                "import counter\n"
                "import report\n\n\n"
                "def test_status():\n"
                "    counter.VALUE = 12\n"
                '    assert report.status() == "value=12"\n\n\n'
                "def test_status_zero():\n"
                "    counter.VALUE = 0\n"
                '    assert report.status() == "value=0"\n\n\n'
                "def test_banner_regression():\n"
                '    assert report.banner() == "counter-report"\n'
            ),
            "ops": [
                ("replace", "report.py", _b4a_old, _b4a_new),
                ("replace", "report.py", _b4b_old, _b4b_new),
            ],
            "expect_targets": {"report.py"},
        },
        {
            "instruction": (
                "ops_log.py 新增 last_op()：返回最后一条 op 字典；日志为空返回 None。"
            ),
            "tests": (
                "import ops_log\n\n\n"
                "def test_last_op():\n"
                "    ops_log.OPS.clear()\n"
                '    ops_log.push({"op": "bump", "delta": 3})\n'
                '    assert ops_log.last_op() == {"op": "bump", "delta": 3}\n\n\n'
                "def test_last_op_empty():\n"
                "    ops_log.OPS.clear()\n"
                "    assert ops_log.last_op() is None\n\n\n"
                "def test_length_regression():\n"
                "    ops_log.OPS.clear()\n"
                '    ops_log.push({"op": "bump", "delta": 1})\n'
                "    assert ops_log.length() == 1\n"
            ),
            "ops": [("replace", "ops_log.py", _b5_old, _b5_new)],
            "expect_targets": {"ops_log.py"},
        },
        {
            "instruction": (
                "counter.py 新增 undo_last()：弹出最后一条日志，若是 bump 则反向扣减 "
                "delta，把该条压入 UNDONE 并返回它；日志为空返回 None"
                "（需要补充 ops_log.py 的 OPS 与 UNDONE）。"
            ),
            "tests": (
                "import counter\n"
                "import ops_log\n"
                "import report\n\n\n"
                "def test_undo_last():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    ops_log.UNDONE.clear()\n"
                "    counter.bump(5)\n"
                "    counter.bump(3)\n"
                "    op = counter.undo_last()\n"
                '    assert op == {"op": "bump", "delta": 3}\n'
                "    assert counter.VALUE == 5\n"
                "    assert ops_log.length() == 1\n"
                '    assert ops_log.UNDONE == [{"op": "bump", "delta": 3}]\n\n\n'
                "def test_undo_empty():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    assert counter.undo_last() is None\n\n\n"
                "def test_status_regression():\n"
                "    counter.VALUE = 9\n"
                '    assert report.status() == "value=9"\n'
            ),
            "ops": [
                ("replace", "ops_log.py", _b6a_old, _b6a_new),
                ("replace", "counter.py", _b6b_old, _b6b_new),
                ("replace", "counter.py", _b6c_old, _b6c_new),
            ],
            "expect_targets": {"counter.py", "ops_log.py"},
        },
        {
            "instruction": (
                "counter.py 新增 redo_last()：从 UNDONE 弹出一条并按其 delta "
                "重新 bump，返回新值；栈空返回 None。"
            ),
            "tests": (
                "import counter\n"
                "import ops_log\n\n\n"
                "def test_redo():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    ops_log.UNDONE.clear()\n"
                "    counter.bump(5)\n"
                "    counter.undo_last()\n"
                "    assert counter.redo_last() == 5\n"
                "    assert counter.VALUE == 5\n"
                "    assert ops_log.length() == 1\n"
                "    assert ops_log.UNDONE == []\n\n\n"
                "def test_redo_empty():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    ops_log.UNDONE.clear()\n"
                "    assert counter.redo_last() is None\n\n\n"
                "def test_undo_regression():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    ops_log.UNDONE.clear()\n"
                "    counter.bump(4)\n"
                '    assert counter.undo_last() == {"op": "bump", "delta": 4}\n'
                "    assert counter.VALUE == 0\n"
            ),
            "ops": [("replace", "counter.py", _b7_old, _b7_new)],
            "expect_targets": {"counter.py"},
        },
        {
            "instruction": (
                "ops_log.py 新增 compact()：压缩日志——清空 OPS 并返回压缩前的条目数。"
            ),
            "tests": (
                "import ops_log\n\n\n"
                "def test_compact():\n"
                "    ops_log.OPS.clear()\n"
                "    for d in (1, 2, 3):\n"
                '        ops_log.push({"op": "bump", "delta": d})\n'
                "    assert ops_log.compact() == 3\n"
                "    assert ops_log.length() == 0\n\n\n"
                "def test_compact_empty():\n"
                "    ops_log.OPS.clear()\n"
                "    assert ops_log.compact() == 0\n\n\n"
                "def test_last_op_regression():\n"
                "    ops_log.OPS.clear()\n"
                '    ops_log.push({"op": "bump", "delta": 7})\n'
                '    assert ops_log.last_op() == {"op": "bump", "delta": 7}\n'
            ),
            "ops": [("replace", "ops_log.py", _b8_old, _b8_new)],
            "expect_targets": {"ops_log.py"},
        },
        {
            "instruction": (
                "请修改 ops_log.py 中的 compact：压缩后应保留最近 2 条"
                "（当前全部清空），返回值仍为压缩前条目数。"
            ),
            "tests": (
                "import ops_log\n\n\n"
                "def test_compact_keeps_two():\n"
                "    ops_log.OPS.clear()\n"
                "    for d in (1, 2, 3, 4, 5):\n"
                '        ops_log.push({"op": "bump", "delta": d})\n'
                "    assert ops_log.compact() == 5\n"
                "    assert ops_log.length() == 2\n"
                "    assert ops_log.OPS == [\n"
                '        {"op": "bump", "delta": 4}, {"op": "bump", "delta": 5}\n'
                "    ]\n\n\n"
                "def test_compact_short_log():\n"
                "    ops_log.OPS.clear()\n"
                '    ops_log.push({"op": "bump", "delta": 1})\n'
                "    ops_log.compact()\n"
                "    assert ops_log.length() == 1\n\n\n"
                "def test_compact_empty_regression():\n"
                "    ops_log.OPS.clear()\n"
                "    assert ops_log.compact() == 0\n"
            ),
            "ops": [("replace", "ops_log.py", _b9_old, _b9_new)],
            "expect_targets": {"ops_log.py"},
        },
        {
            "instruction": (
                "请修改 counter.py 中的 bump：delta 为 0 时抛 ValueError"
                "（非零自增行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import counter\n"
                "import ops_log\n"
                "import report\n\n\n"
                "def test_bump_zero():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                "        counter.bump(0)\n\n\n"
                "def test_bump_ok():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    counter.bump(2)\n"
                "    assert counter.VALUE == 2\n"
                "    assert ops_log.length() == 1\n\n\n"
                "def test_full_chain():\n"
                "    counter.VALUE = 0\n"
                "    ops_log.OPS.clear()\n"
                "    ops_log.UNDONE.clear()\n"
                "    counter.bump(6)\n"
                "    counter.bump(4)\n"
                '    assert counter.undo_last() == {"op": "bump", "delta": 4}\n'
                "    assert counter.redo_last() == 10\n"
                "    assert ops_log.compact() == 2\n"
                "    assert ops_log.length() == 2\n"
                '    assert report.status() == "value=10"\n'
            ),
            "ops": [("replace", "counter.py", _b10_old, _b10_new)],
            "expect_targets": {"counter.py"},
        },
    ],
    info_points=[
        {"id": "ip_bump_records", "type": "implementation",
         "value": "bump 记 {'op': 'bump', 'delta'} 到 OPS",
         "locator": "instruction:step3 + counter.py",
         "needed_by_steps": [3, 6, 7],
         "redundant_in_instruction": True},
        {"id": "ip_undo_invert", "type": "implementation",
         "value": "undo 反向扣减 delta 并把 op 压入 UNDONE",
         "locator": "instruction:step6 + counter.py",
         "needed_by_steps": [6, 7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_compact_keep2", "type": "critical_data",
         "value": "compact 保留条数 0（step8）→2（step9 改约）",
         "locator": "instruction:step8 + instruction:step9",
         "needed_by_steps": [8, 9, 10],
         "redundant_in_instruction": True},
        {"id": "ip_ops_shape", "type": "history",
         "value": "OPS/UNDONE 为 op 字典列表",
         "locator": "ops_log.py after step2 + assistant history",
         "needed_by_steps": [5, 6, 8, 9],
         "redundant_in_instruction": False},
        {"id": "ip_status_binding", "type": "history",
         "value": "report 以 import counter 读取实时 VALUE",
         "locator": "report.py after step4 + assistant history",
         "needed_by_steps": [4, 10],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ LF5 ind_long_graph
# 变体 a：邻接表图（无向→加权→有向→bfs→dfs 遍历改约）

_msh_a = (
    '"""Mesh graph."""\n\n\n'
    "NODES = []\n\n\n"
    "ADJ = {}\n\n\n"
    "def add_node(name):\n"
    "    if name not in NODES:\n"
    "        NODES.append(name)\n\n\n"
    "def add_edge(a, b):\n"
    "    ADJ.setdefault(a, []).append(b)\n"
    "    ADJ.setdefault(b, []).append(a)\n"
)
_cst_a = (
    '"""Edge costs."""\n\n\n'
    "EDGE_W = {}\n\n\n"
    "def set_w(a, b, w):\n"
    "    EDGE_W[(a, b)] = w\n"
    "    EDGE_W[(b, a)] = w\n"
)
_wlk_a = (
    '"""Walk helpers."""\n\n\n'
    "def tag():\n"
    '    return "walk"\n'
)
_g1_old = "def add_edge(a, b):\n    ADJ.setdefault(a, []).append(b)\n    ADJ.setdefault(b, []).append(a)"
_g1_new = _g1_old + "\n\n\ndef has_node(name):\n    return name in NODES"
_g2_old = _g1_old
_g2_new = (
    "def add_edge(a, b):\n"
    "    if b in ADJ.get(a, []):\n"
    "        return False\n"
    "    ADJ.setdefault(a, []).append(b)\n"
    "    ADJ.setdefault(b, []).append(a)\n"
    "    return True"
)
_g3a_old = '"""Mesh graph."""'
_g3a_new = '"""Mesh graph."""\nimport costs'
_g3b_old = "def has_node(name):\n    return name in NODES"
_g3b_new = _g3b_old + (
    "\n\n\ndef weight(a, b):\n"
    "    if b not in ADJ.get(a, []):\n"
    "        return None\n"
    "    return costs.EDGE_W.get((a, b), 1)"
)
_g4a_old = '"""Walk helpers."""'
_g4a_new = '"""Walk helpers."""\nfrom mesh import ADJ'
_g4b_old = 'def tag():\n    return "walk"'
_g4b_new = _g4b_old + (
    "\n\n\ndef degree_line(name):\n"
    '    return f"{name}={len(ADJ.get(name, []))}"'
)
_g5_old = (
    "def add_edge(a, b):\n"
    "    if b in ADJ.get(a, []):\n"
    "        return False\n"
    "    ADJ.setdefault(a, []).append(b)\n"
    "    ADJ.setdefault(b, []).append(a)\n"
    "    return True"
)
_g5_new = (
    "def add_edge(a, b):\n"
    "    if b in ADJ.get(a, []):\n"
    "        return False\n"
    "    ADJ.setdefault(a, []).append(b)\n"
    "    ADJ.setdefault(b, [])\n"
    "    return True"
)
_g6_old = 'def degree_line(name):\n    return f"{name}={len(ADJ.get(name, []))}"'
_g6_new = _g6_old + (
    "\n\n\ndef bfs(start):\n"
    "    seen = [start]\n"
    "    queue = [start]\n"
    "    while queue:\n"
    "        cur = queue.pop(0)\n"
    "        for nb in ADJ.get(cur, []):\n"
    "            if nb not in seen:\n"
    "                seen.append(nb)\n"
    "                queue.append(nb)\n"
    "    return seen"
)
_g7_old = (
    "def weight(a, b):\n"
    "    if b not in ADJ.get(a, []):\n"
    "        return None\n"
    "    return costs.EDGE_W.get((a, b), 1)"
)
_g7_new = _g7_old + (
    "\n\n\ndef connected(a, b):\n"
    "    if a == b:\n"
    "        return True\n"
    "    seen = {a}\n"
    "    stack = [a]\n"
    "    while stack:\n"
    "        cur = stack.pop()\n"
    "        for nb in ADJ.get(cur, []):\n"
    "            if nb == b:\n"
    "                return True\n"
    "            if nb not in seen:\n"
    "                seen.add(nb)\n"
    "                stack.append(nb)\n"
    "    return False"
)
_g8a_old = "EDGE_W = {}"
_g8a_new = "EDGE_W = {}\nDEFAULT_W = 2"
_g8b_old = "    return costs.EDGE_W.get((a, b), 1)"
_g8b_new = "    return costs.EDGE_W.get((a, b), costs.DEFAULT_W)"
_g9_old = (
    "def bfs(start):\n"
    "    seen = [start]\n"
    "    queue = [start]\n"
    "    while queue:\n"
    "        cur = queue.pop(0)\n"
    "        for nb in ADJ.get(cur, []):\n"
    "            if nb not in seen:\n"
    "                seen.append(nb)\n"
    "                queue.append(nb)\n"
    "    return seen"
)
_g9_new = (
    "def dfs(start):\n"
    "    seen = []\n"
    "    stack = [start]\n"
    "    while stack:\n"
    "        cur = stack.pop()\n"
    "        if cur in seen:\n"
    "            continue\n"
    "        seen.append(cur)\n"
    "        for nb in reversed(ADJ.get(cur, [])):\n"
    "            stack.append(nb)\n"
    "    return seen"
)
T(
    id="ind_L05a",
    family="ind_long_graph",
    type="graph_semantics_evolution",
    difficulty="long",
    focus="10 步邻接表图演进：查点→去重加边→加权→度数消费方→有向改约→可达→默认权改约→遍历改约",
    files={"mesh.py": _msh_a, "costs.py": _cst_a, "walk.py": _wlk_a},
    steps=[
        {
            "instruction": (
                "mesh.py 新增 has_node(name)：节点存在返回 True，否则返回 False。"
            ),
            "tests": (
                "import mesh\n\n\n"
                "def test_has_node():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    mesh.add_node("a")\n'
                '    assert mesh.has_node("a") is True\n'
                '    assert mesh.has_node("zz") is False\n\n\n'
                "def test_add_node_regression():\n"
                "    mesh.NODES.clear()\n"
                '    mesh.add_node("a")\n'
                '    mesh.add_node("a")\n'
                '    assert mesh.NODES == ["a"]\n'
            ),
            "ops": [("replace", "mesh.py", _g1_old, _g1_new)],
            "expect_targets": {"mesh.py"},
        },
        {
            "instruction": (
                "请修改 mesh.py 中的 add_edge：重复加同一条边不再追加，"
                "返回是否真的新增了边（新边 True，重复 False）。"
            ),
            "tests": (
                "import mesh\n\n\n"
                "def test_add_edge_dedup():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    assert mesh.add_edge("a", "b") is True\n'
                '    assert mesh.add_edge("a", "b") is False\n'
                '    assert mesh.ADJ["a"] == ["b"]\n\n\n'
                "def test_symmetric():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    assert mesh.ADJ["b"] == ["a"]\n\n\n'
                "def test_has_node_regression():\n"
                "    mesh.NODES.clear()\n"
                '    mesh.add_node("a")\n'
                '    assert mesh.has_node("a") is True\n'
            ),
            "ops": [("replace", "mesh.py", _g2_old, _g2_new)],
            "expect_targets": {"mesh.py"},
        },
        {
            "instruction": (
                "mesh.py 新增 weight(a, b)：边存在时返回权值（未设置过返回 1），"
                "边不存在返回 None（权值表在 costs 模块）。"
            ),
            "tests": (
                "import mesh\n"
                "import costs\n\n\n"
                "def test_weight_set():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    costs.EDGE_W.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    costs.set_w("a", "b", 5)\n'
                '    assert mesh.weight("a", "b") == 5\n\n\n'
                "def test_weight_default():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    costs.EDGE_W.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    assert mesh.weight("a", "b") == 1\n\n\n'
                "def test_weight_missing_edge():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    costs.EDGE_W.clear()\n"
                '    assert mesh.weight("x", "y") is None\n\n\n'
                "def test_dedup_regression():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    assert mesh.add_edge("a", "b") is True\n'
                '    assert mesh.add_edge("a", "b") is False\n'
            ),
            "ops": [
                ("replace", "mesh.py", _g3a_old, _g3a_new),
                ("replace", "mesh.py", _g3b_old, _g3b_new),
            ],
            "expect_targets": {"mesh.py"},
        },
        {
            "instruction": (
                "walk.py 新增 degree_line(name)：输出 'name=deg'，"
                "deg 为该点在 mesh.py 的 ADJ 中的邻居数（需要补充 import）。"
            ),
            "tests": (
                "import mesh\n"
                "import walk\n\n\n"
                "def test_degree_line():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    mesh.add_edge("a", "c")\n'
                '    assert walk.degree_line("a") == "a=2"\n\n\n'
                "def test_degree_zero():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    mesh.add_node("solo")\n'
                '    assert walk.degree_line("solo") == "solo=0"\n\n\n'
                "def test_tag_regression():\n"
                '    assert walk.tag() == "walk"\n\n\n'
                "def test_weight_regression():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    import costs\n"
                "    costs.EDGE_W.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    assert mesh.weight("a", "b") == 1\n'
            ),
            "ops": [
                ("replace", "walk.py", _g4a_old, _g4a_new),
                ("replace", "walk.py", _g4b_old, _g4b_new),
            ],
            "expect_targets": {"walk.py", "mesh.py"},
        },
        {
            "instruction": (
                "请修改 mesh.py 中的 add_edge：图改为有向——只登记 a 到 b 的边，"
                "不再登记反向边（重复判定仍按同向）。"
            ),
            "tests": (
                "import mesh\n"
                "import costs\n\n\n"
                "def test_directed_edge():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    costs.EDGE_W.clear()\n"
                '    mesh.add_edge("x", "y")\n'
                '    assert mesh.ADJ["x"] == ["y"]\n'
                '    assert mesh.ADJ["y"] == []\n'
                '    assert mesh.weight("y", "x") is None\n\n\n'
                "def test_directed_dedup():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    assert mesh.add_edge("x", "y") is True\n'
                '    assert mesh.add_edge("x", "y") is False\n\n\n'
                "def test_degree_regression():\n"
                "    import walk\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    mesh.add_edge("a", "c")\n'
                '    assert walk.degree_line("a") == "a=2"\n'
            ),
            "ops": [("replace", "mesh.py", _g5_old, _g5_new)],
            "expect_targets": {"mesh.py"},
        },
        {
            "instruction": (
                "walk.py 新增 bfs(start)：按广度优先返回访问序列，"
                "邻居按 ADJ 列表顺序（需要补充 import）。"
            ),
            "tests": (
                "import mesh\n"
                "import walk\n\n\n"
                "def test_bfs():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    for n in ("a", "b", "c", "d"):\n'
                "        mesh.add_node(n)\n"
                '    mesh.add_edge("a", "b")\n'
                '    mesh.add_edge("a", "c")\n'
                '    mesh.add_edge("b", "d")\n'
                '    assert walk.bfs("a") == ["a", "b", "c", "d"]\n\n\n'
                "def test_bfs_isolated():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    mesh.add_node("solo")\n'
                '    assert walk.bfs("solo") == ["solo"]\n\n\n'
                "def test_directed_regression():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    mesh.add_edge("x", "y")\n'
                '    assert mesh.ADJ["y"] == []\n'
            ),
            "ops": [("replace", "walk.py", _g6_old, _g6_new)],
            "expect_targets": {"walk.py"},
        },
        {
            "instruction": (
                "mesh.py 新增 connected(a, b)：判断 a 能否沿有向边到达 b"
                "（同一点返回 True）。"
            ),
            "tests": (
                "import mesh\n"
                "import walk\n\n\n"
                "def _chain():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    for n in ("a", "b", "c"):\n'
                "        mesh.add_node(n)\n"
                '    mesh.add_edge("a", "b")\n'
                '    mesh.add_edge("b", "c")\n\n\n'
                "def test_connected_yes():\n"
                "    _chain()\n"
                '    assert mesh.connected("a", "c") is True\n\n\n'
                "def test_connected_no():\n"
                "    _chain()\n"
                '    assert mesh.connected("c", "a") is False\n\n\n'
                "def test_connected_self():\n"
                "    _chain()\n"
                '    assert mesh.connected("c", "c") is True\n\n\n'
                "def test_bfs_regression():\n"
                "    _chain()\n"
                '    assert walk.bfs("a") == ["a", "b", "c"]\n'
            ),
            "ops": [("replace", "mesh.py", _g7_old, _g7_new)],
            "expect_targets": {"mesh.py"},
        },
        {
            "instruction": (
                "costs.py 新增 DEFAULT_W = 2；请修改 mesh.py 中的 weight："
                "未设置权值的边改为返回 DEFAULT_W（当前返回 1）。"
            ),
            "tests": (
                "import costs\n"
                "import mesh\n\n\n"
                "def test_default_w_constant():\n"
                "    assert costs.DEFAULT_W == 2\n\n\n"
                "def test_weight_uses_default():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    costs.EDGE_W.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    assert mesh.weight("a", "b") == 2\n\n\n'
                "def test_connected_regression():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    assert mesh.connected("a", "b") is True\n'
                '    assert mesh.connected("b", "a") is False\n'
            ),
            "ops": [
                ("replace", "costs.py", _g8a_old, _g8a_new),
                ("replace", "mesh.py", _g8b_old, _g8b_new),
            ],
            "expect_targets": {"costs.py", "mesh.py"},
        },
        {
            "instruction": (
                "将 walk.py 中的 bfs 重命名为 dfs，"
                "并把遍历规则改为深度优先前序（邻接列表顺序）。"
            ),
            "tests": (
                "import mesh\n"
                "import walk\n"
                "import costs\n\n\n"
                "def test_dfs_order():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                '    for n in ("a", "b", "c", "d"):\n'
                "        mesh.add_node(n)\n"
                '    mesh.add_edge("a", "b")\n'
                '    mesh.add_edge("a", "c")\n'
                '    mesh.add_edge("b", "d")\n'
                '    assert walk.dfs("a") == ["a", "b", "d", "c"]\n\n\n'
                "def test_old_name_gone():\n"
                '    assert not hasattr(walk, "bfs")\n\n\n'
                "def test_default_w_regression():\n"
                "    assert costs.DEFAULT_W == 2\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    costs.EDGE_W.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    assert mesh.weight("a", "b") == 2\n'
            ),
            "ops": [("replace", "walk.py", _g9_old, _g9_new)],
            "expect_targets": {"walk.py"},
        },
        {
            "instruction": (
                "请修改 costs.py 中的 DEFAULT_W：应从 2 改为 5，"
                "未设置权值的边随之更新。"
            ),
            "tests": (
                "import costs\n"
                "import mesh\n"
                "import walk\n\n\n"
                "def test_default_w_updated():\n"
                "    assert costs.DEFAULT_W == 5\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    costs.EDGE_W.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    assert mesh.weight("a", "b") == 5\n\n\n'
                "def test_set_w_still_wins():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    costs.EDGE_W.clear()\n"
                '    mesh.add_edge("a", "b")\n'
                '    costs.set_w("a", "b", 9)\n'
                '    assert mesh.weight("a", "b") == 9\n\n\n'
                "def test_full_chain():\n"
                "    mesh.NODES.clear()\n"
                "    mesh.ADJ.clear()\n"
                "    costs.EDGE_W.clear()\n"
                '    for n in ("a", "b", "c"):\n'
                "        mesh.add_node(n)\n"
                '    assert mesh.has_node("a") is True\n'
                '    assert mesh.add_edge("a", "b") is True\n'
                '    assert mesh.add_edge("a", "b") is False\n'
                '    mesh.add_edge("a", "c")\n'
                '    assert mesh.connected("a", "c") is True\n'
                '    assert walk.dfs("a") == ["a", "b", "c"]\n'
                '    assert walk.degree_line("a") == "a=2"\n'
            ),
            "ops": [("replace", "costs.py", "DEFAULT_W = 2\n", "DEFAULT_W = 5\n")],
            "expect_targets": {"costs.py"},
        },
    ],
    info_points=[
        {"id": "ip_add_edge_contract", "type": "implementation",
         "value": "add_edge 去重返回 bool；step5 起只登记同向",
         "locator": "instruction:step2 + instruction:step5 + mesh.py",
         "needed_by_steps": [2, 5, 7],
         "redundant_in_instruction": True},
        {"id": "ip_weight_rule", "type": "implementation",
         "value": "边存在返回 EDGE_W.get((a,b), DEFAULT_W)，否则 None",
         "locator": "instruction:step3 + instruction:step8 + mesh.py",
         "needed_by_steps": [3, 8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_default_w", "type": "critical_data",
         "value": "DEFAULT_W：2（step8）→5（step10）",
         "locator": "instruction:step8 + instruction:step10",
         "needed_by_steps": [8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_adj_shape", "type": "history",
         "value": "ADJ 为 {点: 邻居列表}；step5 起只含出边",
         "locator": "mesh.py after step1 + assistant history",
         "needed_by_steps": [4, 5, 6, 9],
         "redundant_in_instruction": False},
        {"id": "ip_traversal_switch", "type": "history",
         "value": "step9 起 dfs 深度优先前序取代 bfs 广度优先",
         "locator": "walk.py after step9 + step10 回归 eval",
         "needed_by_steps": [9, 10],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：边表图（边字典→加权→有向→跳数上限改约）

_net_b = (
    '"""Edge-centric net."""\n\n\n'
    "NODES = set()\n\n\n"
    "LINKS = {}\n\n\n"
    "def add_node(n):\n"
    "    NODES.add(n)\n\n\n"
    "def link(u, v):\n"
    '    LINKS[(u, v)] = True\n'
    '    LINKS[(v, u)] = True\n'
)
_scan_b = (
    '"""Link scanner."""\n\n\n'
    "def tag():\n"
    '    return "scan"\n'
)
_toll_b = (
    '"""Toll helpers."""\n\n\n'
    "def label(u, v):\n"
    '    return f"{u}->{v}"\n'
)
_n1_old = (
    "def link(u, v):\n"
    '    LINKS[(u, v)] = True\n'
    '    LINKS[(v, u)] = True'
)
_n1_new = _n1_old + "\n\n\ndef nodes():\n    return sorted(NODES)"
_n2_old = _n1_old
_n2_new = (
    "def link(u, v):\n"
    "    if u == v:\n"
    '        raise ValueError("self loop")\n'
    '    LINKS[(u, v)] = True\n'
    '    LINKS[(v, u)] = True'
)
_n3a_old = (
    "def link(u, v):\n"
    "    if u == v:\n"
    '        raise ValueError("self loop")\n'
    '    LINKS[(u, v)] = True\n'
    '    LINKS[(v, u)] = True'
)
_n3a_new = (
    "def link(u, v, w=1):\n"
    "    if u == v:\n"
    '        raise ValueError("self loop")\n'
    '    LINKS[(u, v)] = w\n'
    '    LINKS[(v, u)] = w'
)
_n3b_old = "def nodes():\n    return sorted(NODES)"
_n3b_new = _n3b_old + "\n\n\ndef weight(u, v):\n    return LINKS.get((u, v))"
_n4a_old = '"""Link scanner."""'
_n4a_new = '"""Link scanner."""\nimport nets'
_n4b_old = 'def tag():\n    return "scan"'
_n4b_new = _n4b_old + "\n\n\ndef link_count():\n    return len(nets.LINKS)"
_n5a_old = '"""Toll helpers."""'
_n5a_new = '"""Toll helpers."""\nimport nets'
_n5b_old = 'def label(u, v):\n    return f"{u}->{v}"'
_n5b_new = _n5b_old + (
    "\n\n\ndef heaviest():\n"
    "    if not nets.LINKS:\n"
    "        return None\n"
    "    best = max(nets.LINKS.values())\n"
    "    pairs = [k for k, w in nets.LINKS.items() if w == best]\n"
    "    return min(pairs)"
)
_n6_old = (
    "def link(u, v, w=1):\n"
    "    if u == v:\n"
    '        raise ValueError("self loop")\n'
    '    LINKS[(u, v)] = w\n'
    '    LINKS[(v, u)] = w'
)
_n6_new = (
    "def link(u, v, w=1):\n"
    "    if u == v:\n"
    '        raise ValueError("self loop")\n'
    '    LINKS[(u, v)] = w'
)
_n7_old = "def weight(u, v):\n    return LINKS.get((u, v))"
_n7_new = _n7_old + (
    "\n\n\ndef reachable(u):\n"
    "    seen = {u}\n"
    "    stack = [u]\n"
    "    while stack:\n"
    "        cur = stack.pop()\n"
    "        for (a, b) in LINKS:\n"
    "            if a == cur and b not in seen:\n"
    "                seen.add(b)\n"
    "                stack.append(b)\n"
    "    return sorted(seen)"
)
_n8a_old = "LINKS = {}"
_n8a_new = "LINKS = {}\nCAP = 6"
_n8b_old = (
    "def reachable(u):\n"
    "    seen = {u}\n"
    "    stack = [u]\n"
    "    while stack:\n"
    "        cur = stack.pop()\n"
    "        for (a, b) in LINKS:\n"
    "            if a == cur and b not in seen:\n"
    "                seen.add(b)\n"
    "                stack.append(b)\n"
    "    return sorted(seen)"
)
_n8b_new = _n8b_old + (
    "\n\n\ndef capped(u, v):\n"
    "    w = weight(u, v)\n"
    "    if w is None:\n"
    "        return None\n"
    "    return min(w, CAP)"
)
_n9_old = _n8b_old
_n9_new = (
    "def reachable(u):\n"
    "    seen = {u: 0}\n"
    "    frontier = [u]\n"
    "    hops = 0\n"
    "    while frontier and hops < 2:\n"
    "        nxt = []\n"
    "        for cur in frontier:\n"
    "            for (a, b) in LINKS:\n"
    "                if a == cur and b not in seen:\n"
    "                    seen[b] = hops + 1\n"
    "                    nxt.append(b)\n"
    "        frontier = nxt\n"
    "        hops += 1\n"
    "    return sorted(seen)"
)
T(
    id="ind_L05b",
    family="ind_long_graph",
    type="graph_semantics_evolution",
    difficulty="long",
    focus="10 步边表图演进：列点→自环拒绝→加权→计数→极值消费方→有向改约→可达→封顶→跳数改约",
    files={"nets.py": _net_b, "scan.py": _scan_b, "toll.py": _toll_b},
    steps=[
        {
            "instruction": "nets.py 新增 nodes()：返回 NODES 的排序列表。",
            "tests": (
                "import nets\n\n\n"
                "def test_nodes_sorted():\n"
                "    nets.NODES.clear()\n"
                '    nets.add_node("b")\n'
                '    nets.add_node("a")\n'
                '    assert nets.nodes() == ["a", "b"]\n\n\n'
                "def test_nodes_empty():\n"
                "    nets.NODES.clear()\n"
                "    assert nets.nodes() == []\n\n\n"
                "def test_add_node_regression():\n"
                "    nets.NODES.clear()\n"
                '    nets.add_node("x")\n'
                '    assert "x" in nets.NODES\n'
            ),
            "ops": [("replace", "nets.py", _n1_old, _n1_new)],
            "expect_targets": {"nets.py"},
        },
        {
            "instruction": (
                "请修改 nets.py 中的 link：u 与 v 相同时抛 ValueError"
                "（正常连边行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import nets\n\n\n"
                "def test_self_loop_rejected():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        nets.link("a", "a")\n\n\n'
                "def test_link_ok():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b")\n'
                '    assert nets.LINKS[("a", "b")] is True\n'
                '    assert nets.LINKS[("b", "a")] is True\n\n\n'
                "def test_nodes_regression():\n"
                "    nets.NODES.clear()\n"
                '    nets.add_node("b")\n'
                '    nets.add_node("a")\n'
                '    assert nets.nodes() == ["a", "b"]\n'
            ),
            "ops": [("replace", "nets.py", _n2_old, _n2_new)],
            "expect_targets": {"nets.py"},
        },
        {
            "instruction": (
                "请修改 nets.py 中的 link：签名改为 link(u, v, w=1)，"
                "把 w 记入 LINKS（双向登记）；并新增 weight(u, v)："
                "返回该边权重，缺失返回 None。"
            ),
            "tests": (
                "import nets\n\n\n"
                "def test_link_weight():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b", 4)\n'
                '    assert nets.weight("a", "b") == 4\n'
                '    assert nets.weight("b", "a") == 4\n\n\n'
                "def test_weight_default():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b")\n'
                '    assert nets.weight("a", "b") == 1\n\n\n'
                "def test_weight_missing():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    assert nets.weight("x", "y") is None\n\n\n'
                "def test_self_loop_regression():\n"
                "    import pytest\n"
                "    nets.LINKS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        nets.link("a", "a")\n'
            ),
            "ops": [
                ("replace", "nets.py", _n3a_old, _n3a_new),
                ("replace", "nets.py", _n3b_old, _n3b_new),
            ],
            "expect_targets": {"nets.py"},
        },
        {
            "instruction": (
                "scan.py 新增 link_count()：返回 LINKS 中的条目数"
                "（需要从 nets 模块导入）。"
            ),
            "tests": (
                "import nets\n"
                "import scan\n\n\n"
                "def test_link_count():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b", 2)\n'
                "    assert scan.link_count() == 2\n\n\n"
                "def test_link_count_empty():\n"
                "    nets.LINKS.clear()\n"
                "    assert scan.link_count() == 0\n\n\n"
                "def test_tag_regression():\n"
                '    assert scan.tag() == "scan"\n\n\n'
                "def test_weight_regression():\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b", 3)\n'
                '    assert nets.weight("a", "b") == 3\n'
            ),
            "ops": [
                ("replace", "scan.py", _n4a_old, _n4a_new),
                ("replace", "scan.py", _n4b_old, _n4b_new),
            ],
            "expect_targets": {"scan.py"},
        },
        {
            "instruction": (
                "toll.py 新增 heaviest()：返回权重最大的 (u, v) 元组"
                "（并列取字典序最小），无边返回 None（需要补充 import）。"
            ),
            "tests": (
                "import nets\n"
                "import toll\n"
                "import scan\n\n\n"
                "def test_heaviest():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b", 5)\n'
                '    nets.link("b", "c", 2)\n'
                '    assert toll.heaviest() == ("a", "b")\n\n\n'
                "def test_heaviest_empty():\n"
                "    nets.LINKS.clear()\n"
                "    assert toll.heaviest() is None\n\n\n"
                "def test_label_regression():\n"
                '    assert toll.label("x", "y") == "x->y"\n\n\n'
                "def test_count_regression():\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b")\n'
                "    assert scan.link_count() == 2\n"
            ),
            "ops": [
                ("replace", "toll.py", _n5a_old, _n5a_new),
                ("replace", "toll.py", _n5b_old, _n5b_new),
            ],
            "expect_targets": {"toll.py"},
        },
        {
            "instruction": (
                "请修改 nets.py 中的 link：图改为有向——只登记 (u, v)，"
                "不再登记 (v, u)（自环拒绝与权重默认值不变）。"
            ),
            "tests": (
                "import nets\n"
                "import toll\n"
                "import scan\n\n\n"
                "def test_directed_link():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("x", "y", 3)\n'
                '    assert nets.LINKS[("x", "y")] == 3\n'
                '    assert ("y", "x") not in nets.LINKS\n\n\n'
                "def test_directed_heaviest():\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b", 5)\n'
                '    assert toll.heaviest() == ("a", "b")\n\n\n'
                "def test_count_regression():\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b")\n'
                "    assert scan.link_count() == 1\n\n\n"
                "def test_weight_regression():\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b", 4)\n'
                '    assert nets.weight("a", "b") == 4\n'
                '    assert nets.weight("b", "a") is None\n'
            ),
            "ops": [("replace", "nets.py", _n6_old, _n6_new)],
            "expect_targets": {"nets.py"},
        },
        {
            "instruction": (
                "nets.py 新增 reachable(u)：返回沿有向边可达的点集合（含自身），"
                "按字典序排序。"
            ),
            "tests": (
                "import nets\n\n\n"
                "def _chain():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    for n in ("a", "b", "c", "d"):\n'
                "        nets.add_node(n)\n"
                '    nets.link("a", "b")\n'
                '    nets.link("b", "c")\n'
                '    nets.link("c", "d")\n\n\n'
                "def test_reachable_full():\n"
                "    _chain()\n"
                '    assert nets.reachable("a") == ["a", "b", "c", "d"]\n\n\n'
                "def test_reachable_backward():\n"
                "    _chain()\n"
                '    assert nets.reachable("d") == ["d"]\n\n\n'
                "def test_directed_regression():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("x", "y", 3)\n'
                '    assert ("y", "x") not in nets.LINKS\n'
            ),
            "ops": [("replace", "nets.py", _n7_old, _n7_new)],
            "expect_targets": {"nets.py"},
        },
        {
            "instruction": (
                "nets.py 新增 CAP = 6 与 capped(u, v)：返回该边权重与 CAP 的较小者，"
                "无边返回 None。"
            ),
            "tests": (
                "import nets\n\n\n"
                "def test_cap_constant():\n"
                "    assert nets.CAP == 6\n\n\n"
                "def test_capped():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b", 9)\n'
                '    assert nets.capped("a", "b") == 6\n'
                '    nets.link("b", "c", 2)\n'
                '    assert nets.capped("b", "c") == 2\n\n\n'
                "def test_capped_missing():\n"
                "    nets.LINKS.clear()\n"
                '    assert nets.capped("x", "y") is None\n\n\n'
                "def test_reachable_regression():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b")\n'
                '    nets.link("b", "c")\n'
                '    assert nets.reachable("a") == ["a", "b", "c"]\n'
            ),
            "ops": [
                ("replace", "nets.py", _n8a_old, _n8a_new),
                ("replace", "nets.py", _n8b_old, _n8b_new),
            ],
            "expect_targets": {"nets.py"},
        },
        {
            "instruction": (
                "请修改 nets.py 中的 reachable：改为最多 2 跳可达"
                "（自身、1 跳、2 跳），仍按字典序排序。"
            ),
            "tests": (
                "import nets\n\n\n"
                "def _chain():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    for n in ("a", "b", "c", "d"):\n'
                "        nets.add_node(n)\n"
                '    nets.link("a", "b")\n'
                '    nets.link("b", "c")\n'
                '    nets.link("c", "d")\n\n\n'
                "def test_reachable_two_hops():\n"
                "    _chain()\n"
                '    assert nets.reachable("a") == ["a", "b", "c"]\n\n\n'
                "def test_reachable_one_hop():\n"
                "    _chain()\n"
                '    assert nets.reachable("c") == ["c", "d"]\n\n\n'
                "def test_cap_regression():\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b", 9)\n'
                '    assert nets.capped("a", "b") == 6\n'
            ),
            "ops": [("replace", "nets.py", _n9_old, _n9_new)],
            "expect_targets": {"nets.py"},
        },
        {
            "instruction": (
                "请修改 nets.py 中的 CAP：应从 6 改为 3，capped 结果随之更新。"
            ),
            "tests": (
                "import nets\n"
                "import scan\n"
                "import toll\n\n\n"
                "def test_cap_updated():\n"
                "    assert nets.CAP == 3\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    nets.link("a", "b", 9)\n'
                '    assert nets.capped("a", "b") == 3\n'
                '    nets.link("b", "c", 2)\n'
                '    assert nets.capped("b", "c") == 2\n\n\n'
                "def test_full_chain():\n"
                "    nets.NODES.clear()\n"
                "    nets.LINKS.clear()\n"
                '    for n in ("a", "b", "c"):\n'
                "        nets.add_node(n)\n"
                '    assert nets.nodes() == ["a", "b", "c"]\n'
                '    nets.link("a", "b", 4)\n'
                '    nets.link("b", "c", 7)\n'
                "    assert scan.link_count() == 2\n"
                '    assert toll.heaviest() == ("b", "c")\n'
                '    assert nets.reachable("a") == ["a", "b", "c"]\n'
                '    assert nets.capped("b", "c") == 3\n'
            ),
            "ops": [("replace", "nets.py", "CAP = 6\n", "CAP = 3\n")],
            "expect_targets": {"nets.py"},
        },
    ],
    info_points=[
        {"id": "ip_link_contract", "type": "implementation",
         "value": "link 拒绝自环；step6 起只登记 (u, v)",
         "locator": "instruction:step2 + instruction:step6 + nets.py",
         "needed_by_steps": [2, 3, 6],
         "redundant_in_instruction": True},
        {"id": "ip_weight_storage", "type": "implementation",
         "value": "LINKS 存权重，weight(u, v) 直接取值",
         "locator": "instruction:step3 + nets.py",
         "needed_by_steps": [3, 5, 8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_cap_value", "type": "critical_data",
         "value": "CAP：6（step8）→3（step10）",
         "locator": "instruction:step8 + instruction:step10",
         "needed_by_steps": [8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_links_shape", "type": "history",
         "value": "LINKS 为 {(u, v): 权重} 字典",
         "locator": "nets.py after step1 + assistant history",
         "needed_by_steps": [4, 5, 7, 9],
         "redundant_in_instruction": False},
        {"id": "ip_directed_consequence", "type": "history",
         "value": "有向化后反向 weight 为 None、可达只看出边",
         "locator": "nets.py after step6 + assistant history",
         "needed_by_steps": [7, 9],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ LF6 ind_long_protocol
# 变体 a：管道分隔帧（v1 编解码→校验→v2 字段→兼容层→版本协商）

_cod_a = (
    '"""Pipe codec."""\n\n\n'
    "def encode(kind, body):\n"
    '    return kind + "|" + body\n\n\n'
    "def decode(text):\n"
    '    return text.split("|", 1)\n'
)
_ver_a = (
    '"""Frame checks."""\n\n\n'
    "def kind_of(text):\n"
    '    return text.split("|", 1)[0]\n'
)
_gw_a = (
    '"""Gateway."""\n\n\n'
    "def addr():\n"
    '    return "gw-1"\n'
)
_p1_old = "def decode(text):\n    return text.split(\"|\", 1)"
_p1_new = (
    "def decode(text):\n"
    '    if "|" not in text:\n'
    '        raise ValueError("frame")\n'
    '    kind, body = text.split("|", 1)\n'
    '    if kind.startswith("v") and len(kind) > 1 and kind[1:].isdigit():\n'
    '        raise ValueError("version")\n'
    "    return (kind, body)"
)
_p2a_old = '"""Frame checks."""'
_p2a_new = '"""Frame checks."""\nimport codec'
_p2b_old = 'def kind_of(text):\n    return text.split("|", 1)[0]'
_p2b_new = _p2b_old + (
    "\n\n\ndef check(text):\n"
    "    try:\n"
    "        codec.decode(text)\n"
    "        return True\n"
    "    except ValueError:\n"
    "        return False"
)
_p3_old = _p1_old
_p3_new = _p1_old  # placeholder unused; decode changed at step1
_p4_old = (
    "def decode(text):\n"
    '    if "|" not in text:\n'
    '        raise ValueError("frame")\n'
    '    kind, body = text.split("|", 1)\n'
    '    if kind.startswith("v") and len(kind) > 1 and kind[1:].isdigit():\n'
    '        raise ValueError("version")\n'
    "    return (kind, body)"
)
_p4_new = _p4_old + (
    "\n\n\ndef encode2(kind, body, tag):\n"
    '    return "v2|" + kind + "|" + body + "|" + tag\n\n\n'
    "def decode2(text):\n"
    '    parts = text.split("|")\n'
    '    if len(parts) != 4 or parts[0] != "v2":\n'
    '        raise ValueError("frame2")\n'
    "    return (parts[1], parts[2], parts[3])"
)
_p5_old = (
    "def decode2(text):\n"
    '    parts = text.split("|")\n'
    '    if len(parts) != 4 or parts[0] != "v2":\n'
    '        raise ValueError("frame2")\n'
    "    return (parts[1], parts[2], parts[3])"
)
_p5_new = _p5_old + (
    "\n\n\ndef decode_any(text):\n"
    '    if text.startswith("v2|"):\n'
    "        return decode2(text)\n"
    "    return decode(text)"
)
_p6a_old = '"""Gateway."""'
_p6a_new = '"""Gateway."""\nimport codec'
_p6b_old = 'def addr():\n    return "gw-1"'
_p6b_new = _p6b_old + (
    "\n\n\ndef route(text):\n"
    "    frame = codec.decode_any(text)\n"
    "    return frame[0]"
)
_p7_old = (
    "def check(text):\n"
    "    try:\n"
    "        codec.decode(text)\n"
    "        return True\n"
    "    except ValueError:\n"
    "        return False"
)
_p7_new = (
    "def check(text):\n"
    "    try:\n"
    "        codec.decode_any(text)\n"
    "        return True\n"
    "    except ValueError:\n"
    "        return False"
)
_p8_old = (
    "def decode_any(text):\n"
    '    if text.startswith("v2|"):\n'
    "        return decode2(text)\n"
    "    return decode(text)"
)
_p8_new = _p8_old + (
    "\n\n\ndef version_of(text):\n"
    '    if text.startswith("v2|"):\n'
    "        return 2\n"
    '    if "|" in text:\n'
    "        return 1\n"
    '    raise ValueError("frame")'
)
_p9_old = (
    "def version_of(text):\n"
    '    if text.startswith("v2|"):\n'
    "        return 2\n"
    '    if "|" in text:\n'
    "        return 1\n"
    '    raise ValueError("frame")'
)
_p9_new = _p9_old + (
    "\n\n\ndef negotiate(theirs):\n"
    "    common = [v for v in theirs if v in (1, 2)]\n"
    "    if not common:\n"
    '        raise ValueError("version")\n'
    "    return max(common)"
)
_p10_old = (
    "def negotiate(theirs):\n"
    "    common = [v for v in theirs if v in (1, 2)]\n"
    "    if not common:\n"
    '        raise ValueError("version")\n'
    "    return max(common)"
)
_p10_new = (
    "def negotiate(theirs):\n"
    "    common = [v for v in theirs if v in (1, 2)]\n"
    "    if not common:\n"
    "        return 1\n"
    "    return max(common)"
)
_p11_old = (
    "def encode2(kind, body, tag):\n"
    '    return "v2|" + kind + "|" + body + "|" + tag'
)
_p11_new = (
    "def encode2(kind, body, tag):\n"
    '    return "v2|" + kind + "|" + tag + "|" + body'
)
_p12_old = (
    "def decode2(text):\n"
    '    parts = text.split("|")\n'
    '    if len(parts) != 4 or parts[0] != "v2":\n'
    '        raise ValueError("frame2")\n'
    "    return (parts[1], parts[2], parts[3])"
)
_p12_new = (
    "def decode2(text):\n"
    '    parts = text.split("|")\n'
    '    if len(parts) != 4 or parts[0] != "v2":\n'
    '        raise ValueError("frame2")\n'
    "    return (parts[1], parts[3], parts[2])"
)
T(
    id="ind_L06a",
    family="ind_long_protocol",
    type="protocol_version_evolution",
    difficulty="long",
    focus="10 步协议演进：v1 解码→校验→v2 字段→兼容层→路由→协商→协商回退→字段顺序改约",
    files={"codec.py": _cod_a, "verify.py": _ver_a, "gateway.py": _gw_a},
    steps=[
        {
            "instruction": (
                "请修改 codec.py 中的 decode：应返回 (kind, body) 元组；"
                "缺 '|' 或 kind 形如 v 加数字（版本保留头）时抛 ValueError。"
            ),
            "tests": (
                "import pytest\n"
                "import codec\n\n\n"
                "def test_decode_tuple():\n"
                '    assert codec.decode("hi|there") == ("hi", "there")\n\n\n'
                "def test_decode_missing_sep():\n"
                "    with pytest.raises(ValueError):\n"
                '        codec.decode("lonely")\n\n\n'
                "def test_version_prefix_rejected():\n"
                "    with pytest.raises(ValueError):\n"
                '        codec.decode("v9|x")\n\n\n'
                "def test_encode_regression():\n"
                '    assert codec.encode("hi", "there") == "hi|there"\n'
            ),
            "ops": [("replace", "codec.py", _p1_old, _p1_new)],
            "expect_targets": {"codec.py"},
        },
        {
            "instruction": (
                "verify.py 新增 check(text)：用 codec 的 decode 解析，"
                "成功返回 True，抛 ValueError 返回 False（需要补充 import）。"
            ),
            "tests": (
                "import verify\n\n\n"
                "def test_check_ok():\n"
                '    assert verify.check("hi|there") is True\n\n\n'
                "def test_check_bad():\n"
                '    assert verify.check("lonely") is False\n\n\n'
                "def test_kind_regression():\n"
                '    assert verify.kind_of("hi|there") == "hi"\n'
            ),
            "ops": [
                ("replace", "verify.py", _p2a_old, _p2a_new),
                ("replace", "verify.py", _p2b_old, _p2b_new),
            ],
            "expect_targets": {"verify.py", "codec.py"},
        },
        {
            "instruction": (
                "codec.py 新增 encode2(kind, body, tag) 与 decode2(text)："
                "v2 帧格式为 'v2|kind|body|tag'，decode2 返回 (kind, body, tag)，"
                "格式不符抛 ValueError。"
            ),
            "tests": (
                "import pytest\n"
                "import codec\n\n\n"
                "def test_encode2():\n"
                '    assert codec.encode2("login", "alice", "urgent") == "v2|login|alice|urgent"\n\n\n'
                "def test_decode2():\n"
                '    assert codec.decode2("v2|login|alice|urgent") == ("login", "alice", "urgent")\n\n\n'
                "def test_decode2_bad():\n"
                "    with pytest.raises(ValueError):\n"
                '        codec.decode2("v1|a|b|c")\n'
                "    with pytest.raises(ValueError):\n"
                '        codec.decode2("v2|a|b")\n\n\n'
                "def test_decode_regression():\n"
                '    assert codec.decode("k|v") == ("k", "v")\n'
            ),
            "ops": [
                ("replace", "codec.py", _p4_old, _p4_new),
            ],
            "expect_targets": {"codec.py"},
        },
        {
            "instruction": (
                "codec.py 新增 decode_any(text)：v2 帧按 decode2 解析返回三元组，"
                "普通 v1 帧按 decode 解析返回二元组，坏帧抛 ValueError。"
            ),
            "tests": (
                "import pytest\n"
                "import codec\n\n\n"
                "def test_any_v1():\n"
                '    assert codec.decode_any("k|v") == ("k", "v")\n\n\n'
                "def test_any_v2():\n"
                '    assert codec.decode_any("v2|login|alice|urgent") == ("login", "alice", "urgent")\n\n\n'
                "def test_any_bad():\n"
                "    with pytest.raises(ValueError):\n"
                '        codec.decode_any("junk")\n'
                "    with pytest.raises(ValueError):\n"
                '        codec.decode_any("v3|a|b|c")\n\n\n'
                "def test_decode2_regression():\n"
                '    assert codec.decode2("v2|k|b|t") == ("k", "b", "t")\n'
            ),
            "ops": [("replace", "codec.py", _p5_old, _p5_new)],
            "expect_targets": {"codec.py"},
        },
        {
            "instruction": (
                "gateway.py 新增 route(text)：用 codec.py 的 decode_any 解析帧"
                "并返回其 kind 字段（需要补充 import）。"
            ),
            "tests": (
                "import gateway\n"
                "import codec\n\n\n"
                "def test_route_v1():\n"
                '    assert gateway.route("hi|there") == "hi"\n\n\n'
                "def test_route_v2():\n"
                '    assert gateway.route("v2|ping|body|tag") == "ping"\n\n\n'
                "def test_addr_regression():\n"
                '    assert gateway.addr() == "gw-1"\n\n\n'
                "def test_decode_any_regression():\n"
                '    assert codec.decode_any("k|v") == ("k", "v")\n'
            ),
            "ops": [
                ("replace", "gateway.py", _p6a_old, _p6a_new),
                ("replace", "gateway.py", _p6b_old, _p6b_new),
            ],
            "expect_targets": {"gateway.py", "codec.py"},
        },
        {
            "instruction": (
                "请修改 verify.py 中的 check：应改用 decode_any 解析，"
                "使 v2 帧也返回 True（v1 行为不变）。"
            ),
            "tests": (
                "import verify\n\n\n"
                "def test_check_v1():\n"
                '    assert verify.check("hi|there") is True\n\n\n'
                "def test_check_v2():\n"
                '    assert verify.check("v2|login|alice|urgent") is True\n\n\n'
                "def test_check_bad():\n"
                '    assert verify.check("lonely") is False\n\n\n'
                "def test_kind_regression():\n"
                '    assert verify.kind_of("hi|there") == "hi"\n'
            ),
            "ops": [("replace", "verify.py", _p7_old, _p7_new)],
            "expect_targets": {"verify.py", "codec.py"},
        },
        {
            "instruction": (
                "codec.py 新增 version_of(text)：帧头为 v2 返回 2，"
                "普通 v1 帧返回 1，无分隔符的坏帧抛 ValueError。"
            ),
            "tests": (
                "import pytest\n"
                "import codec\n\n\n"
                "def test_version_v2():\n"
                '    assert codec.version_of("v2|a|b|c") == 2\n\n\n'
                "def test_version_v1():\n"
                '    assert codec.version_of("hi|there") == 1\n\n\n'
                "def test_version_bad():\n"
                "    with pytest.raises(ValueError):\n"
                '        codec.version_of("lonely")\n\n\n'
                "def test_decode_any_regression():\n"
                '    assert codec.decode_any("v2|k|b|t") == ("k", "b", "t")\n'
            ),
            "ops": [("replace", "codec.py", _p8_old, _p8_new)],
            "expect_targets": {"codec.py"},
        },
        {
            "instruction": (
                "codec.py 新增 negotiate(theirs)：在本端支持的 [1, 2] 与对端列表求交集，"
                "返回交集中最高版本；无交集抛 ValueError。"
            ),
            "tests": (
                "import pytest\n"
                "import codec\n\n\n"
                "def test_negotiate_max():\n"
                "    assert codec.negotiate([1, 2]) == 2\n\n\n"
                "def test_negotiate_subset():\n"
                "    assert codec.negotiate([2]) == 2\n\n\n"
                "def test_negotiate_empty():\n"
                "    with pytest.raises(ValueError):\n"
                "        codec.negotiate([3, 4])\n\n\n"
                "def test_version_regression():\n"
                '    assert codec.version_of("hi|there") == 1\n'
            ),
            "ops": [("replace", "codec.py", _p9_old, _p9_new)],
            "expect_targets": {"codec.py"},
        },
        {
            "instruction": (
                "请修改 codec.py 中的 negotiate：无交集时不再抛错，"
                "改为回退返回 1（有交集行为不变）。"
            ),
            "tests": (
                "import codec\n\n\n"
                "def test_negotiate_fallback():\n"
                "    assert codec.negotiate([3, 4]) == 1\n\n\n"
                "def test_negotiate_common_regression():\n"
                "    assert codec.negotiate([1, 2]) == 2\n"
                "    assert codec.negotiate([2]) == 2\n\n\n"
                "def test_version_regression():\n"
                '    assert codec.version_of("v2|a|b|c") == 2\n'
            ),
            "ops": [("replace", "codec.py", _p10_old, _p10_new)],
            "expect_targets": {"codec.py"},
        },
        {
            "instruction": (
                "请修改 codec.py 中的 encode2 与 decode2："
                "v2 帧字段顺序改为 kind、tag、body（返回仍为 (kind, body, tag)），"
                "兼容与校验路径随之更新。"
            ),
            "tests": (
                "import codec\n"
                "import verify\n\n\n"
                "def test_v2_order():\n"
                '    assert codec.encode2("login", "alice", "urgent") == "v2|login|urgent|alice"\n'
                '    assert codec.decode2("v2|login|urgent|alice") == ("login", "alice", "urgent")\n\n\n'
                "def test_decode_any_new_order():\n"
                '    assert codec.decode_any("v2|login|urgent|alice") == ("login", "alice", "urgent")\n\n\n'
                "def test_v1_regression():\n"
                '    assert codec.encode("k", "v") == "k|v"\n'
                '    assert codec.decode("k|v") == ("k", "v")\n\n\n'
                "def test_check_regression():\n"
                '    assert verify.check("v2|login|urgent|alice") is True\n'
                "    assert codec.negotiate([3, 4]) == 1\n"
            ),
            "ops": [
                ("replace", "codec.py", _p11_old, _p11_new),
                ("replace", "codec.py", _p12_old, _p12_new),
            ],
            "expect_targets": {"codec.py"},
        },
    ],
    info_points=[
        {"id": "ip_decode_contract", "type": "interface",
         "value": "decode 返回 (kind, body)；坏帧与版本保留头抛 ValueError",
         "locator": "instruction:step1 + codec.py",
         "needed_by_steps": [1, 2, 4],
         "redundant_in_instruction": True},
        {"id": "ip_v2_format", "type": "critical_data",
         "value": "v2 帧 'v2|kind|body|tag'（step10 改为 kind|tag|body）",
         "locator": "instruction:step3 + instruction:step10",
         "needed_by_steps": [3, 4, 5, 10],
         "redundant_in_instruction": True},
        {"id": "ip_versions", "type": "critical_data",
         "value": "本端支持 1、2；无交集回退 1（step9）",
         "locator": "instruction:step8 + instruction:step9",
         "needed_by_steps": [8, 9],
         "redundant_in_instruction": True},
        {"id": "ip_frame_shape", "type": "history",
         "value": "v1 帧为 'kind|body' 二段",
         "locator": "codec.py after step1 + assistant history",
         "needed_by_steps": [2, 4, 7],
         "redundant_in_instruction": False},
        {"id": "ip_check_path", "type": "history",
         "value": "verify.check 经 codec 解析（step2 引入，step6 换路径）",
         "locator": "verify.py after step2 + assistant history",
         "needed_by_steps": [2, 6],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：冒号分隔帧（空载荷拒绝→字段解析→v2 序号帧→兼容→协商策略改约）

_wir_b = (
    '"""Wire format."""\n\n\n'
    "def pack(cmd, payload):\n"
    '    return cmd + ":" + payload\n\n\n'
    "def unpack(text):\n"
    "    cmd, payload = text.split(\":\", 1)\n"
    "    return cmd, payload\n"
)
_grd_b = (
    '"""Guard rails."""\n\n\n'
    "def is_safe(text):\n"
    '    return ":" in text\n'
)
_brg_b = (
    '"""Bridge."""\n\n\n'
    "def name():\n"
    '    return "bridge-0"\n'
)
_w1_old = (
    "def unpack(text):\n"
    "    cmd, payload = text.split(\":\", 1)\n"
    "    return cmd, payload"
)
_w1_new = (
    "def unpack(text):\n"
    '    if ":" not in text:\n'
    '        raise ValueError("frame")\n'
    "    cmd, payload = text.split(\":\", 1)\n"
    "    if not payload.strip():\n"
    '        raise ValueError("payload")\n'
    "    return cmd, payload"
)
_w2_old = _w1_new
_w2_new = _w1_new + (
    "\n\n\ndef fields(payload):\n"
    "    out = {}\n"
    '    for seg in payload.split(";"):\n'
    '        if "=" not in seg:\n'
    '            raise ValueError("field")\n'
    '        k, v = seg.split("=", 1)\n'
    "        out[k] = v\n"
    "    return out"
)
_w3a_old = '"""Guard rails."""'
_w3a_new = '"""Guard rails."""\nimport wire'
_w3b_old = 'def is_safe(text):\n    return ":" in text'
_w3b_new = (
    "def is_safe(text):\n"
    "    try:\n"
    "        cmd, payload = wire.unpack(text)\n"
    "        wire.fields(payload)\n"
    "        return True\n"
    "    except ValueError:\n"
    "        return False"
)
_w4a_old = '"""Bridge."""'
_w4a_new = '"""Bridge."""\nimport wire'
_w4b_old = 'def name():\n    return "bridge-0"'
_w4b_new = _w4b_old + (
    "\n\n\ndef dispatch(text):\n"
    "    try:\n"
    "        cmd, payload = wire.unpack(text)\n"
    "        wire.fields(payload)\n"
    "        return cmd\n"
    "    except ValueError:\n"
    "        return None"
)
_w5_old = _w2_new
_w5_new = _w2_new + (
    "\n\n\ndef pack2(seq, cmd, payload):\n"
    '    return "#" + str(seq) + " " + cmd + ":" + payload\n\n\n'
    "def unpack2(text):\n"
    '    if not text.startswith("#"):\n'
    '        raise ValueError("frame2")\n'
    '    head, rest = text[1:].split(" ", 1)\n'
    "    if not head.isdigit():\n"
    '        raise ValueError("seq")\n'
    "    cmd, payload = rest.split(\":\", 1)\n"
    "    return (int(head), cmd, payload)"
)
_w6_old = (
    "def unpack2(text):\n"
    '    if not text.startswith("#"):\n'
    '        raise ValueError("frame2")\n'
    '    head, rest = text[1:].split(" ", 1)\n'
    "    if not head.isdigit():\n"
    '        raise ValueError("seq")\n'
    "    cmd, payload = rest.split(\":\", 1)\n"
    "    return (int(head), cmd, payload)"
)
_w6_new = _w6_old + (
    "\n\n\ndef unpack_any(text):\n"
    '    if text.startswith("#"):\n'
    "        return unpack2(text)\n"
    "    return unpack(text)"
)
_w7_old = (
    "def dispatch(text):\n"
    "    try:\n"
    "        cmd, payload = wire.unpack(text)\n"
    "        wire.fields(payload)\n"
    "        return cmd\n"
    "    except ValueError:\n"
    "        return None"
)
_w7_new = (
    "def dispatch(text):\n"
    "    try:\n"
    "        frame = wire.unpack_any(text)\n"
    "        cmd = frame[1] if len(frame) == 3 else frame[0]\n"
    "        wire.fields(frame[-1])\n"
    "        return cmd\n"
    "    except ValueError:\n"
    "        return None"
)
_w8a_old = '"""Wire format."""'
_w8a_new = '"""Wire format."""\n\nMAX_SEQ = 999'
_w8b_old = (
    "def unpack2(text):\n"
    '    if not text.startswith("#"):\n'
    '        raise ValueError("frame2")\n'
    '    head, rest = text[1:].split(" ", 1)\n'
    "    if not head.isdigit():\n"
    '        raise ValueError("seq")\n'
    "    cmd, payload = rest.split(\":\", 1)\n"
    "    return (int(head), cmd, payload)"
)
_w8b_new = (
    "def unpack2(text):\n"
    '    if not text.startswith("#"):\n'
    '        raise ValueError("frame2")\n'
    '    head, rest = text[1:].split(" ", 1)\n'
    "    if not head.isdigit():\n"
    '        raise ValueError("seq")\n'
    "    if int(head) > MAX_SEQ:\n"
    '        raise ValueError("seq")\n'
    "    cmd, payload = rest.split(\":\", 1)\n"
    "    return (int(head), cmd, payload)"
)
_w9_old = _w4b_old + "\n\n\n" + _w7_new
_w9_new = _w9_old + (
    "\n\n\ndef negotiate(versions):\n"
    "    common = [v for v in versions if v in (1, 2)]\n"
    "    if not common:\n"
    "        return None\n"
    "    return min(common)"
)
_w10_old = (
    "def negotiate(versions):\n"
    "    common = [v for v in versions if v in (1, 2)]\n"
    "    if not common:\n"
    "        return None\n"
    "    return min(common)"
)
_w10_new = (
    "def negotiate(versions):\n"
    "    common = [v for v in versions if v in (1, 2)]\n"
    "    if not common:\n"
    "        return None\n"
    "    return max(common)"
)
T(
    id="ind_L06b",
    family="ind_long_protocol",
    type="protocol_version_evolution",
    difficulty="long",
    focus="10 步冒号帧协议演进：空载荷拒绝→字段解析→安全闸→路由→v2 序号帧→兼容→序号上限→协商改约",
    files={"wire.py": _wir_b, "guard.py": _grd_b, "bridge.py": _brg_b},
    steps=[
        {
            "instruction": (
                "请修改 wire.py 中的 unpack：payload 为空白时抛 ValueError"
                "（正常解包行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import wire\n\n\n"
                "def test_empty_payload_rejected():\n"
                "    with pytest.raises(ValueError):\n"
                '        wire.unpack("cmd:")\n\n\n'
                "def test_ok_unpack():\n"
                '    assert wire.unpack("cmd: a=1 ") == ("cmd", " a=1 ")\n\n\n'
                "def test_no_colon():\n"
                "    with pytest.raises(ValueError):\n"
                '        wire.unpack("nocolon")\n\n\n'
                "def test_pack_regression():\n"
                '    assert wire.pack("cmd", "a=1") == "cmd:a=1"\n'
            ),
            "ops": [("replace", "wire.py", _w1_old, _w1_new)],
            "expect_targets": {"wire.py"},
        },
        {
            "instruction": (
                "wire.py 新增 fields(payload)：按 ';' 切段解析 'k=v' 为字典，"
                "段缺 '=' 时抛 ValueError。"
            ),
            "tests": (
                "import pytest\n"
                "import wire\n\n\n"
                "def test_fields():\n"
                '    assert wire.fields("a=1;b=2") == {"a": "1", "b": "2"}\n\n\n'
                "def test_fields_bad():\n"
                "    with pytest.raises(ValueError):\n"
                '        wire.fields("oops")\n\n\n'
                "def test_fields_single():\n"
                '    assert wire.fields("only=one") == {"only": "one"}\n\n\n'
                "def test_unpack_regression():\n"
                "    with pytest.raises(ValueError):\n"
                '        wire.unpack("cmd:")\n'
            ),
            "ops": [("replace", "wire.py", _w2_old, _w2_new)],
            "expect_targets": {"wire.py"},
        },
        {
            "instruction": (
                "请修改 guard.py 中的 is_safe：改为经 wire.py 的 unpack 与 fields "
                "完整校验，坏帧返回 False（仅含 ':' 不再算安全）。"
            ),
            "tests": (
                "import guard\n\n\n"
                "def test_safe_ok():\n"
                '    assert guard.is_safe("cmd:a=1;b=2") is True\n\n\n'
                "def test_safe_empty_payload():\n"
                '    assert guard.is_safe("cmd:") is False\n\n\n'
                "def test_safe_bad_field():\n"
                '    assert guard.is_safe("cmd:oops") is False\n'
            ),
            "ops": [
                ("replace", "guard.py", _w3a_old, _w3a_new),
                ("replace", "guard.py", _w3b_old, _w3b_new),
            ],
            "expect_targets": {"guard.py", "wire.py"},
        },
        {
            "instruction": (
                "bridge.py 新增 dispatch(text)：用 wire.py 的 unpack 解出 cmd、"
                "fields 解析 payload，坏帧返回 None（需要补充 import）。"
            ),
            "tests": (
                "import bridge\n"
                "import guard\n\n\n"
                "def test_dispatch():\n"
                '    assert bridge.dispatch("ping:a=1;b=2") == "ping"\n\n\n'
                "def test_dispatch_bad():\n"
                '    assert bridge.dispatch("cmd:") is None\n'
                '    assert bridge.dispatch("ping:oops") is None\n\n\n'
                "def test_name_regression():\n"
                '    assert bridge.name() == "bridge-0"\n\n\n'
                "def test_safe_regression():\n"
                '    assert guard.is_safe("cmd:") is False\n'
            ),
            "ops": [
                ("replace", "bridge.py", _w4a_old, _w4a_new),
                ("replace", "bridge.py", _w4b_old, _w4b_new),
            ],
            "expect_targets": {"bridge.py", "wire.py"},
        },
        {
            "instruction": (
                "wire.py 新增 pack2(seq, cmd, payload) 与 unpack2(text)："
                "v2 帧格式 '#seq cmd:payload'，unpack2 返回 (seq, cmd, payload)，"
                "帧头或 seq 非数字抛 ValueError。"
            ),
            "tests": (
                "import pytest\n"
                "import wire\n\n\n"
                "def test_pack2():\n"
                '    assert wire.pack2(3, "ping", "a=1") == "#3 ping:a=1"\n\n\n'
                "def test_unpack2():\n"
                '    assert wire.unpack2("#3 ping:a=1") == (3, "ping", "a=1")\n\n\n'
                "def test_unpack2_bad():\n"
                "    with pytest.raises(ValueError):\n"
                '        wire.unpack2("ping:a=1")\n'
                "    with pytest.raises(ValueError):\n"
                '        wire.unpack2("#x ping:a=1")\n\n\n'
                "def test_roundtrip_v1():\n"
                '    assert wire.unpack(wire.pack("k", "v")) == ("k", "v")\n'
            ),
            "ops": [("replace", "wire.py", _w5_old, _w5_new)],
            "expect_targets": {"wire.py"},
        },
        {
            "instruction": (
                "wire.py 新增 unpack_any(text)：'#' 开头走 unpack2 返回三元组，"
                "否则走 unpack 返回二元组，坏帧抛 ValueError。"
            ),
            "tests": (
                "import pytest\n"
                "import wire\n\n\n"
                "def test_any_v1():\n"
                '    assert wire.unpack_any("k:v") == ("k", "v")\n\n\n'
                "def test_any_v2():\n"
                '    assert wire.unpack_any("#7 ping:a=1") == (7, "ping", "a=1")\n\n\n'
                "def test_any_bad():\n"
                "    with pytest.raises(ValueError):\n"
                '        wire.unpack_any("nocolon")\n\n\n'
                "def test_unpack2_regression():\n"
                '    assert wire.unpack2("#1 k:v") == (1, "k", "v")\n'
            ),
            "ops": [("replace", "wire.py", _w6_old, _w6_new)],
            "expect_targets": {"wire.py"},
        },
        {
            "instruction": (
                "请修改 bridge.py 中的 dispatch：改用 wire.py 的 unpack_any 解析，"
                "'#' 帧返回其 cmd 字段，普通帧行为不变。"
            ),
            "tests": (
                "import bridge\n\n\n"
                "def test_dispatch_v2():\n"
                '    assert bridge.dispatch("#2 ping:a=1") == "ping"\n\n\n'
                "def test_dispatch_v1_regression():\n"
                '    assert bridge.dispatch("ping:a=1") == "ping"\n\n\n'
                "def test_dispatch_bad_regression():\n"
                '    assert bridge.dispatch("cmd:") is None\n'
            ),
            "ops": [("replace", "bridge.py", _w7_old, _w7_new)],
            "expect_targets": {"bridge.py", "wire.py"},
        },
        {
            "instruction": (
                "wire.py 新增 MAX_SEQ = 999；unpack2 对超过 MAX_SEQ 的 seq 抛 ValueError"
                "（其余行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import wire\n"
                "import bridge\n\n\n"
                "def test_max_seq_constant():\n"
                "    assert wire.MAX_SEQ == 999\n\n\n"
                "def test_seq_over_limit():\n"
                "    with pytest.raises(ValueError):\n"
                '        wire.unpack2("#1000 k:v")\n\n\n'
                "def test_seq_ok():\n"
                '    assert wire.unpack2("#5 k:v") == (5, "k", "v")\n\n\n'
                "def test_dispatch_regression():\n"
                '    assert bridge.dispatch("#2 ping:a=1") == "ping"\n'
            ),
            "ops": [
                ("replace", "wire.py", _w8a_old, _w8a_new),
                ("replace", "wire.py", _w8b_old, _w8b_new),
            ],
            "expect_targets": {"wire.py"},
        },
        {
            "instruction": (
                "bridge.py 新增 negotiate(versions)：返回对端版本与本端 [1, 2] "
                "的交集中的最小版本，无交集返回 None。"
            ),
            "tests": (
                "import bridge\n\n\n"
                "def test_negotiate_min():\n"
                "    assert bridge.negotiate([1, 2]) == 1\n\n\n"
                "def test_negotiate_subset():\n"
                "    assert bridge.negotiate([2]) == 2\n\n\n"
                "def test_negotiate_none():\n"
                "    assert bridge.negotiate([3, 4]) is None\n\n\n"
                "def test_dispatch_regression():\n"
                '    assert bridge.dispatch("#2 ping:a=1") == "ping"\n'
            ),
            "ops": [("replace", "bridge.py", _w9_old, _w9_new)],
            "expect_targets": {"bridge.py"},
        },
        {
            "instruction": (
                "请修改 bridge.py 中的 negotiate：有交集时应返回最高版本"
                "（当前返回最低），无交集仍返回 None。"
            ),
            "tests": (
                "import bridge\n"
                "import wire\n"
                "import guard\n\n\n"
                "def test_negotiate_max():\n"
                "    assert bridge.negotiate([1, 2]) == 2\n\n\n"
                "def test_negotiate_subset_regression():\n"
                "    assert bridge.negotiate([2]) == 2\n"
                "    assert bridge.negotiate([1]) == 1\n\n\n"
                "def test_negotiate_none_regression():\n"
                "    assert bridge.negotiate([5]) is None\n\n\n"
                "def test_full_chain():\n"
                '    assert wire.unpack_any(wire.pack2(9, "go", "x=1")) == (9, "go", "x=1")\n'
                '    assert guard.is_safe("go:x=1") is True\n'
                '    assert bridge.dispatch("#9 go:x=1") == "go"\n'
                "    assert bridge.negotiate([1, 2, 3]) == 2\n"
            ),
            "ops": [("replace", "bridge.py", _w10_old, _w10_new)],
            "expect_targets": {"bridge.py"},
        },
    ],
    info_points=[
        {"id": "ip_unpack_contract", "type": "interface",
         "value": "unpack 返回 (cmd, payload)；空 payload 拒绝",
         "locator": "instruction:step1 + wire.py",
         "needed_by_steps": [1, 3, 4],
         "redundant_in_instruction": True},
        {"id": "ip_fields_format", "type": "implementation",
         "value": "payload 'k=v;k=v' 解析为字典",
         "locator": "instruction:step2 + wire.py",
         "needed_by_steps": [2, 3, 4],
         "redundant_in_instruction": True},
        {"id": "ip_v2_frame", "type": "critical_data",
         "value": "v2 帧 '#seq cmd:payload'；MAX_SEQ = 999",
         "locator": "instruction:step5 + instruction:step8",
         "needed_by_steps": [5, 6, 8],
         "redundant_in_instruction": True},
        {"id": "ip_wire_shape", "type": "history",
         "value": "pack/unpack 为 ':' 分隔二段",
         "locator": "wire.py after step1 + assistant history",
         "needed_by_steps": [4, 6],
         "redundant_in_instruction": False},
        {"id": "ip_dispatch_path", "type": "history",
         "value": "dispatch 经 unpack_any（step7 决定）",
         "locator": "bridge.py after step7 + assistant history",
         "needed_by_steps": [7, 8, 10],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ LF7 ind_long_repo
# 变体 a：列表仓储（增查→过滤→分页→约束→成年改约）

_shf_a = (
    '"""Record shelf."""\n\n\n'
    "RECORDS = []\n\n\n"
    "def insert(rec):\n"
    "    RECORDS.append(rec)\n"
)
_rul_a = '"""Shelf rules."""\n'
_vws_a = (
    '"""View helpers."""\n\n\n'
    "def heading():\n"
    '    return "shelf"\n'
)
_r1_old = "def insert(rec):\n    RECORDS.append(rec)"
_r1_new = _r1_old + (
    "\n\n\ndef find(name):\n"
    "    for rec in RECORDS:\n"
    '        if rec["name"] == name:\n'
    "            return rec\n"
    "    return None"
)
_r2_old = _r1_old
_r2_new = (
    "def insert(rec):\n"
    "    if any(r[\"name\"] == rec[\"name\"] for r in RECORDS):\n"
    '        raise ValueError("name")\n'
    "    RECORDS.append(rec)"
)
_r3_old = (
    "def find(name):\n"
    "    for rec in RECORDS:\n"
    '        if rec["name"] == name:\n'
    "            return rec\n"
    "    return None"
)
_r3_new = _r3_old + (
    "\n\n\ndef filter_by(min_score):\n"
    "    return [r for r in RECORDS if r[\"score\"] >= min_score]"
)
_r4a_old = '"""View helpers."""'
_r4a_new = '"""View helpers."""\nimport shelf'
_r4b_old = 'def heading():\n    return "shelf"'
_r4b_new = _r4b_old + (
    "\n\n\ndef top_names(n):\n"
    '    ordered = sorted(shelf.RECORDS, key=lambda r: (-r["score"], r["name"]))\n'
    "    return [r[\"name\"] for r in ordered[:n]]"
)
_r5_old = _r3_new
_r5_new = _r3_new + "\n\n\ndef page(offset, limit):\n    return RECORDS[offset:offset + limit]"
_r6_old = (
    "def insert(rec):\n"
    "    if any(r[\"name\"] == rec[\"name\"] for r in RECORDS):\n"
    '        raise ValueError("name")\n'
    "    RECORDS.append(rec)"
)
_r6_new = (
    "def insert(rec):\n"
    "    if any(r[\"name\"] == rec[\"name\"] for r in RECORDS):\n"
    '        raise ValueError("name")\n'
    "    if rec[\"score\"] < 0 or rec[\"score\"] > 100:\n"
    '        raise ValueError("score")\n'
    "    RECORDS.append(rec)"
)
_r7a_old = '"""Record shelf."""'
_r7a_new = '"""Record shelf."""\nfrom rules import MIN_AGE'
_r7b_old = _r5_new
_r7b_new = _r5_new + (
    "\n\n\ndef adults():\n"
    "    return [r for r in RECORDS if r[\"age\"] >= MIN_AGE]"
)
_r8_old = _r4b_new
_r8_new = _r4b_new + (
    "\n\n\ndef summary():\n"
    "    total = len(shelf.RECORDS)\n"
    "    adult = len(shelf.adults())\n"
    '    return f"{total} total, {adult} adult"'
)
_r9_old = (
    "    if rec[\"score\"] < 0 or rec[\"score\"] > 100:\n"
    '        raise ValueError("score")'
)
_r9_new = (
    "    if rec[\"score\"] < 0 or rec[\"score\"] > 200:\n"
    '        raise ValueError("score")'
)
T(
    id="ind_L07a",
    family="ind_long_repo",
    type="repository_query_evolution",
    difficulty="long",
    focus="10 步列表仓储演进：增查→重名约束→过滤→视图消费方→分页→分数约束→成年改约",
    files={"shelf.py": _shf_a, "rules.py": _rul_a, "views.py": _vws_a},
    steps=[
        {
            "instruction": (
                "shelf.py 新增 find(name)：返回首个 name 匹配的记录，没有则返回 None。"
            ),
            "tests": (
                "import shelf\n\n\n"
                "def _seed():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 20, "score": 70})\n'
                '    shelf.insert({"name": "bob", "age": 15, "score": 90})\n\n\n'
                "def test_find():\n"
                "    _seed()\n"
                '    assert shelf.find("bob")["score"] == 90\n\n\n'
                "def test_find_missing():\n"
                "    _seed()\n"
                '    assert shelf.find("zz") is None\n\n\n'
                "def test_insert_regression():\n"
                "    _seed()\n"
                "    assert len(shelf.RECORDS) == 2\n"
            ),
            "ops": [("replace", "shelf.py", _r1_old, _r1_new)],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "请修改 shelf.py 中的 insert：已有同 name 记录时抛 ValueError"
                "（新增不同 name 行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import shelf\n\n\n"
                "def _seed():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 20, "score": 70})\n\n\n'
                "def test_duplicate_rejected():\n"
                "    _seed()\n"
                "    with pytest.raises(ValueError):\n"
                '        shelf.insert({"name": "ann", "age": 21, "score": 80})\n'
                "    assert len(shelf.RECORDS) == 1\n\n\n"
                "def test_new_name_ok():\n"
                "    _seed()\n"
                '    shelf.insert({"name": "bob", "age": 15, "score": 90})\n'
                "    assert len(shelf.RECORDS) == 2\n\n\n"
                "def test_find_regression():\n"
                "    _seed()\n"
                '    assert shelf.find("ann")["age"] == 20\n'
            ),
            "ops": [("replace", "shelf.py", _r2_old, _r2_new)],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "shelf.py 新增 filter_by(min_score)：返回 score 不低于 min_score 的"
                "记录列表（保持原顺序）。"
            ),
            "tests": (
                "import pytest\n"
                "import shelf\n\n\n"
                "def _seed():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 20, "score": 70})\n'
                '    shelf.insert({"name": "bob", "age": 15, "score": 90})\n'
                '    shelf.insert({"name": "cyd", "age": 30, "score": 40})\n\n\n'
                "def test_filter_by():\n"
                "    _seed()\n"
                "    out = shelf.filter_by(70)\n"
                '    assert [r["name"] for r in out] == ["ann", "bob"]\n\n\n'
                "def test_filter_by_none():\n"
                "    _seed()\n"
                "    assert shelf.filter_by(100) == []\n\n\n"
                "def test_duplicate_regression():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 20, "score": 70})\n'
                "    with pytest.raises(ValueError):\n"
                '        shelf.insert({"name": "ann", "age": 1, "score": 1})\n'
            ),
            "ops": [("replace", "shelf.py", _r3_old, _r3_new)],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "views.py 新增 top_names(n)：按 score 降序取 shelf.py 的记录前 n 条"
                "并返回 name 列表（需要补充 import）。"
            ),
            "tests": (
                "import shelf\n"
                "import views\n\n\n"
                "def _seed():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 20, "score": 70})\n'
                '    shelf.insert({"name": "bob", "age": 15, "score": 90})\n'
                '    shelf.insert({"name": "cyd", "age": 30, "score": 40})\n\n\n'
                "def test_top_names():\n"
                "    _seed()\n"
                '    assert views.top_names(2) == ["bob", "ann"]\n\n\n'
                "def test_top_names_all():\n"
                "    _seed()\n"
                '    assert views.top_names(10) == ["bob", "ann", "cyd"]\n\n\n'
                "def test_heading_regression():\n"
                '    assert views.heading() == "shelf"\n\n\n'
                "def test_filter_regression():\n"
                "    _seed()\n"
                '    assert [r["name"] for r in shelf.filter_by(70)] == ["ann", "bob"]\n'
            ),
            "ops": [
                ("replace", "views.py", _r4a_old, _r4a_new),
                ("replace", "views.py", _r4b_old, _r4b_new),
            ],
            "expect_targets": {"views.py", "shelf.py"},
        },
        {
            "instruction": (
                "shelf.py 新增 page(offset, limit)：按当前顺序返回记录切片"
                "offset:offset+limit，越界返回已有部分。"
            ),
            "tests": (
                "import shelf\n"
                "import views\n\n\n"
                "def _seed():\n"
                "    shelf.RECORDS.clear()\n"
                "    for i, s in enumerate((10, 20, 30, 40)):\n"
                '        shelf.insert({"name": f"n{i}", "age": 20, "score": s})\n\n\n'
                "def test_page():\n"
                "    _seed()\n"
                '    assert [r["name"] for r in shelf.page(1, 2)] == ["n1", "n2"]\n\n\n'
                "def test_page_beyond_end():\n"
                "    _seed()\n"
                '    assert [r["name"] for r in shelf.page(3, 5)] == ["n3"]\n\n\n'
                "def test_top_regression():\n"
                "    _seed()\n"
                '    assert views.top_names(1) == ["n3"]\n'
            ),
            "ops": [("replace", "shelf.py", _r5_old, _r5_new)],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "请修改 shelf.py 中的 insert：score 超出 0 到 100 范围时抛 ValueError"
                "（其余校验不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import shelf\n\n\n"
                "def test_score_too_high():\n"
                "    shelf.RECORDS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        shelf.insert({"name": "a", "age": 20, "score": 101})\n\n\n'
                "def test_score_negative():\n"
                "    shelf.RECORDS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        shelf.insert({"name": "a", "age": 20, "score": -1})\n\n\n'
                "def test_score_ok():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "a", "age": 20, "score": 100})\n'
                "    assert len(shelf.RECORDS) == 1\n\n\n"
                "def test_page_regression():\n"
                "    shelf.RECORDS.clear()\n"
                "    for i in range(3):\n"
                '        shelf.insert({"name": f"n{i}", "age": 20, "score": i})\n'
                "    assert len(shelf.page(0, 2)) == 2\n"
            ),
            "ops": [("replace", "shelf.py", _r6_old, _r6_new)],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "rules.py 新增 MIN_AGE = 18；shelf.py 新增 adults()："
                "返回 age 不低于 MIN_AGE 的记录（需要补充 import）。"
            ),
            "tests": (
                "import pytest\n"
                "import rules\n"
                "import shelf\n\n\n"
                "def _seed():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 20, "score": 70})\n'
                '    shelf.insert({"name": "bob", "age": 15, "score": 90})\n'
                '    shelf.insert({"name": "cyd", "age": 30, "score": 40})\n\n\n'
                "def test_min_age_constant():\n"
                "    assert rules.MIN_AGE == 18\n\n\n"
                "def test_adults():\n"
                "    _seed()\n"
                '    assert [r["name"] for r in shelf.adults()] == ["ann", "cyd"]\n\n\n'
                "def test_score_bound_regression():\n"
                "    shelf.RECORDS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        shelf.insert({"name": "a", "age": 1, "score": 101})\n'
            ),
            "ops": [
                ("replace", "rules.py", '"""Shelf rules."""',
                 '"""Shelf rules."""\n\nMIN_AGE = 18'),
                ("replace", "shelf.py", _r7a_old, _r7a_new),
                ("replace", "shelf.py", _r7b_old, _r7b_new),
            ],
            "expect_targets": {"rules.py", "shelf.py"},
        },
        {
            "instruction": (
                "views.py 新增 summary()：输出 'N total, M adult'"
                "（N 为记录总数，M 为 shelf.py 的 adults 数量）。"
            ),
            "tests": (
                "import shelf\n"
                "import views\n\n\n"
                "def _seed():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 20, "score": 70})\n'
                '    shelf.insert({"name": "bob", "age": 15, "score": 90})\n\n\n'
                "def test_summary():\n"
                "    _seed()\n"
                '    assert views.summary() == "2 total, 1 adult"\n\n\n'
                "def test_summary_empty():\n"
                "    shelf.RECORDS.clear()\n"
                '    assert views.summary() == "0 total, 0 adult"\n\n\n'
                "def test_top_regression():\n"
                "    _seed()\n"
                '    assert views.top_names(1) == ["bob"]\n\n\n'
                "def test_adults_regression():\n"
                "    _seed()\n"
                '    assert [r["name"] for r in shelf.adults()] == ["ann"]\n'
            ),
            "ops": [("replace", "views.py", _r8_old, _r8_new)],
            "expect_targets": {"views.py", "shelf.py"},
        },
        {
            "instruction": (
                "请修改 shelf.py 中的 insert：score 上限应从 100 改为 200"
                "（下限与重名拒绝不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import shelf\n"
                "import views\n\n\n"
                "def test_score_150_now_ok():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "a", "age": 20, "score": 150})\n'
                "    assert len(shelf.RECORDS) == 1\n\n\n"
                "def test_score_still_bounded():\n"
                "    shelf.RECORDS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        shelf.insert({"name": "a", "age": 20, "score": 201})\n\n\n'
                "def test_summary_regression():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 20, "score": 70})\n'
                '    shelf.insert({"name": "bob", "age": 15, "score": 90})\n'
                '    assert views.summary() == "2 total, 1 adult"\n'
            ),
            "ops": [("replace", "shelf.py", _r9_old, _r9_new)],
            "expect_targets": {"shelf.py"},
        },
        {
            "instruction": (
                "请修改 rules.py 中的 MIN_AGE：应从 18 改为 21，成年判定随之更新。"
            ),
            "tests": (
                "import rules\n"
                "import shelf\n"
                "import views\n\n\n"
                "def test_min_age_revised():\n"
                "    assert rules.MIN_AGE == 21\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 20, "score": 70})\n'
                '    shelf.insert({"name": "cyd", "age": 30, "score": 40})\n'
                '    assert [r["name"] for r in shelf.adults()] == ["cyd"]\n\n\n'
                "def test_full_chain():\n"
                "    shelf.RECORDS.clear()\n"
                '    shelf.insert({"name": "ann", "age": 25, "score": 80})\n'
                '    shelf.insert({"name": "bob", "age": 15, "score": 95})\n'
                '    shelf.insert({"name": "cyd", "age": 40, "score": 60})\n'
                '    assert shelf.find("bob")["score"] == 95\n'
                '    assert [r["name"] for r in shelf.filter_by(80)] == ["ann", "bob"]\n'
                '    assert views.top_names(2) == ["bob", "ann"]\n'
                '    assert [r["name"] for r in shelf.page(0, 2)] == ["ann", "bob"]\n'
                '    assert views.summary() == "3 total, 2 adult"\n'
            ),
            "ops": [("replace", "rules.py", "MIN_AGE = 18\n", "MIN_AGE = 21\n")],
            "expect_targets": {"rules.py"},
        },
    ],
    info_points=[
        {"id": "ip_find_contract", "type": "interface",
         "value": "find 返回首个 name 匹配记录，缺失返回 None",
         "locator": "instruction:step1 + shelf.py",
         "needed_by_steps": [1, 2, 10],
         "redundant_in_instruction": True},
        {"id": "ip_filter_order", "type": "implementation",
         "value": "filter_by 保持原顺序；top_names 按 score 降序同分按 name 升序",
         "locator": "instruction:step3 + instruction:step4",
         "needed_by_steps": [3, 4, 10],
         "redundant_in_instruction": True},
        {"id": "ip_score_bounds", "type": "critical_data",
         "value": "score ∈ [0,100]（step6）→ 上限 200（step9）",
         "locator": "instruction:step6 + instruction:step9",
         "needed_by_steps": [6, 9, 10],
         "redundant_in_instruction": True},
        {"id": "ip_records_shape", "type": "history",
         "value": "RECORDS 为 dict 列表，键 name/age/score",
         "locator": "shelf.py after step1 + assistant history",
         "needed_by_steps": [3, 4, 5, 7],
         "redundant_in_instruction": False},
        {"id": "ip_min_age_chain", "type": "history",
         "value": "adults 读取 rules.MIN_AGE（step7 引入，step10 改约传播）",
         "locator": "shelf.py after step7 + assistant history",
         "needed_by_steps": [7, 8, 10],
         "redundant_in_instruction": False},
    ],
)

# 变体 b：字典主键仓储（查→过滤→分页→约束→约束改约）

_dpt_b = (
    '"""Keyed depot."""\n\n\n'
    "ROWS = {}\n\n\n"
    "def put(key, rec):\n"
    "    ROWS[key] = rec\n"
)
_qta_b = (
    '"""Quota policy."""\n\n\n'
    "PAGE_SIZE = 3\n"
)
_api_b = (
    '"""Public api."""\n\n\n'
    "def ping():\n"
    '    return "pong"\n'
)
_k1_old = "def put(key, rec):\n    ROWS[key] = rec"
_k1_new = _k1_old + (
    "\n\n\ndef get(key, default=None):\n"
    "    return ROWS.get(key, default)"
)
_k2_old = _k1_old
_k2_new = (
    "def put(key, rec):\n"
    '    if key == "":\n'
    '        raise ValueError("key")\n'
    "    ROWS[key] = rec"
)
_k3_old = (
    "def get(key, default=None):\n"
    "    return ROWS.get(key, default)"
)
_k3_new = _k3_old + (
    "\n\n\ndef where(field, value):\n"
    "    out = []\n"
    "    for key in sorted(ROWS):\n"
    "        rec = ROWS[key]\n"
    "        if rec.get(field) == value:\n"
    "            out.append(rec)\n"
    "    return out"
)
_k4a_old = '"""Public api."""'
_k4a_new = '"""Public api."""\nimport depot'
_k4b_old = 'def ping():\n    return "pong"'
_k4b_new = _k4b_old + (
    "\n\n\ndef count(field, value):\n"
    "    return len(depot.where(field, value))"
)
_k5a_old = '"""Keyed depot."""'
_k5a_new = '"""Keyed depot."""\nimport quota'
_k5b_old = _k3_new
_k5b_new = _k3_new + (
    "\n\n\ndef page(offset):\n"
    "    start = offset * quota.PAGE_SIZE\n"
    "    keys = sorted(ROWS)[start:start + quota.PAGE_SIZE]\n"
    "    return [ROWS[k] for k in keys]"
)
_k6_old = (
    "def put(key, rec):\n"
    '    if key == "":\n'
    '        raise ValueError("key")\n'
    "    ROWS[key] = rec"
)
_k6_new = (
    "def put(key, rec):\n"
    '    if key == "":\n'
    '        raise ValueError("key")\n'
    '    if "name" not in rec:\n'
    '        raise ValueError("name")\n'
    "    ROWS[key] = rec"
)
_k8_old = _k5b_new
_k8_new = _k5b_new + (
    "\n\n\ndef top(field, n):\n"
    "    ordered = sorted(ROWS, key=lambda k: (-ROWS[k][field], k))\n"
    "    return [ROWS[k] for k in ordered[:n]]"
)
_k9_old = _k6_new
_k9_new = (
    "def put(key, rec):\n"
    '    if key == "":\n'
    '        raise ValueError("key")\n'
    '    if "name" not in rec:\n'
    '        raise ValueError("name")\n'
    "    if not str(rec[\"name\"]).strip():\n"
    '        raise ValueError("name")\n'
    "    ROWS[key] = rec"
)
T(
    id="ind_L07b",
    family="ind_long_repo",
    type="repository_query_evolution",
    difficulty="long",
    focus="10 步字典仓储演进：查→空键约束→过滤→计数消费方→分页→缺名约束→排序→约束改约",
    files={"depot.py": _dpt_b, "quota.py": _qta_b, "api.py": _api_b},
    steps=[
        {
            "instruction": (
                "depot.py 新增 get(key, default=None)：返回该 key 的记录，"
                "缺失时返回 default（缺省 None）。"
            ),
            "tests": (
                "import depot\n\n\n"
                "def _seed():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("a", {"name": "ann", "score": 70})\n'
                '    depot.put("b", {"name": "bob", "score": 90})\n\n\n'
                "def test_get():\n"
                "    _seed()\n"
                '    assert depot.get("b")["score"] == 90\n\n\n'
                "def test_get_default():\n"
                "    _seed()\n"
                '    assert depot.get("zz") is None\n'
                '    assert depot.get("zz", {}) == {}\n\n\n'
                "def test_put_regression():\n"
                "    _seed()\n"
                "    assert len(depot.ROWS) == 2\n"
            ),
            "ops": [("replace", "depot.py", _k1_old, _k1_new)],
            "expect_targets": {"depot.py"},
        },
        {
            "instruction": (
                "请修改 depot.py 中的 put：key 为空字符串时抛 ValueError"
                "（正常写入行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import depot\n\n\n"
                "def test_empty_key_rejected():\n"
                "    depot.ROWS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        depot.put("", {"name": "x"})\n\n\n'
                "def test_key_ok():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("k", {"name": "x"})\n'
                '    assert "k" in depot.ROWS\n\n\n'
                "def test_get_regression():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("k", {"name": "x"})\n'
                '    assert depot.get("k")["name"] == "x"\n'
            ),
            "ops": [("replace", "depot.py", _k2_old, _k2_new)],
            "expect_targets": {"depot.py"},
        },
        {
            "instruction": (
                "depot.py 新增 where(field, value)：返回 field 等于 value 的记录列表，"
                "按键升序排列。"
            ),
            "tests": (
                "import depot\n\n\n"
                "def _seed():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("b", {"name": "bob", "team": "red"})\n'
                '    depot.put("a", {"name": "ann", "team": "red"})\n'
                '    depot.put("c", {"name": "cyd", "team": "blue"})\n\n\n'
                "def test_where():\n"
                "    _seed()\n"
                "    out = depot.where(\"team\", \"red\")\n"
                '    assert [r["name"] for r in out] == ["ann", "bob"]\n\n\n'
                "def test_where_none():\n"
                "    _seed()\n"
                '    assert depot.where("team", "green") == []\n\n\n'
                "def test_empty_key_regression():\n"
                "    import pytest\n"
                "    depot.ROWS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        depot.put("", {"name": "x"})\n'
            ),
            "ops": [("replace", "depot.py", _k3_old, _k3_new)],
            "expect_targets": {"depot.py"},
        },
        {
            "instruction": (
                "api.py 新增 count(field, value)：返回 depot.py 中匹配 where 的记录数量"
                "（需要补充 import）。"
            ),
            "tests": (
                "import api\n"
                "import depot\n\n\n"
                "def _seed():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("b", {"name": "bob", "team": "red"})\n'
                '    depot.put("a", {"name": "ann", "team": "red"})\n'
                '    depot.put("c", {"name": "cyd", "team": "blue"})\n\n\n'
                "def test_count():\n"
                "    _seed()\n"
                '    assert api.count("team", "red") == 2\n\n\n'
                "def test_count_zero():\n"
                "    _seed()\n"
                '    assert api.count("team", "green") == 0\n\n\n'
                "def test_ping_regression():\n"
                '    assert api.ping() == "pong"\n\n\n'
                "def test_where_regression():\n"
                "    _seed()\n"
                '    assert [r["name"] for r in depot.where("team", "blue")] == ["cyd"]\n'
            ),
            "ops": [
                ("replace", "api.py", _k4a_old, _k4a_new),
                ("replace", "api.py", _k4b_old, _k4b_new),
            ],
            "expect_targets": {"api.py", "depot.py"},
        },
        {
            "instruction": (
                "depot.py 新增 page(offset)：按 key 升序分页返回记录列表，"
                "每页大小取 quota 模块的 PAGE_SIZE（需要补充 import）。"
            ),
            "tests": (
                "import depot\n"
                "import quota\n"
                "import api\n\n\n"
                "def _seed(n):\n"
                "    depot.ROWS.clear()\n"
                "    for i in range(n):\n"
                '        depot.put(f"k{i:02d}", {"name": f"n{i}", "score": i})\n\n\n'
                "def test_page_size_constant():\n"
                "    assert quota.PAGE_SIZE == 3\n\n\n"
                "def test_page():\n"
                "    _seed(7)\n"
                '    assert [r["name"] for r in depot.page(0)] == ["n0", "n1", "n2"]\n'
                '    assert [r["name"] for r in depot.page(1)] == ["n3", "n4", "n5"]\n'
                '    assert [r["name"] for r in depot.page(2)] == ["n6"]\n\n\n'
                "def test_page_beyond():\n"
                "    _seed(2)\n"
                "    assert depot.page(5) == []\n\n\n"
                "def test_count_regression():\n"
                "    _seed(3)\n"
                '    assert api.count("name", "n1") == 1\n'
            ),
            "ops": [
                ("replace", "depot.py", _k5a_old, _k5a_new),
                ("replace", "depot.py", _k5b_old, _k5b_new),
            ],
            "expect_targets": {"depot.py"},
        },
        {
            "instruction": (
                "请修改 depot.py 中的 put：rec 缺少 name 键时抛 ValueError"
                "（已有校验不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import depot\n\n\n"
                "def test_missing_name():\n"
                "    depot.ROWS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        depot.put("k", {"score": 10})\n\n\n'
                "def test_name_present():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("k", {"name": "x", "score": 10})\n'
                '    assert depot.get("k")["score"] == 10\n\n\n'
                "def test_page_regression():\n"
                "    depot.ROWS.clear()\n"
                "    for i in range(4):\n"
                '        depot.put(f"k{i}", {"name": f"n{i}"})\n'
                "    assert len(depot.page(1)) == 1\n"
            ),
            "ops": [("replace", "depot.py", _k6_old, _k6_new)],
            "expect_targets": {"depot.py"},
        },
        {
            "instruction": (
                "quota.py 中的 PAGE_SIZE 应为 5（当前为 3），分页随之变大。"
            ),
            "tests": (
                "import quota\n"
                "import depot\n\n\n"
                "def test_page_size_updated():\n"
                "    assert quota.PAGE_SIZE == 5\n\n\n"
                "def test_page_follows():\n"
                "    depot.ROWS.clear()\n"
                "    for i in range(7):\n"
                '        depot.put(f"k{i:02d}", {"name": f"n{i}"})\n'
                '    assert [r["name"] for r in depot.page(0)] == [\n'
                '        "n0", "n1", "n2", "n3", "n4"\n'
                "    ]\n"
                '    assert [r["name"] for r in depot.page(1)] == ["n5", "n6"]\n\n\n'
                "def test_name_constraint_regression():\n"
                "    import pytest\n"
                "    depot.ROWS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        depot.put("k", {"score": 1})\n'
            ),
            "ops": [("replace", "quota.py", "PAGE_SIZE = 3\n", "PAGE_SIZE = 5\n")],
            "expect_targets": {"quota.py"},
        },
        {
            "instruction": (
                "depot.py 新增 top(field, n)：按 field 值降序取前 n 条记录"
                "（同值按 key 升序）。"
            ),
            "tests": (
                "import depot\n"
                "import quota\n\n\n"
                "def _seed():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("a", {"name": "ann", "score": 70})\n'
                '    depot.put("b", {"name": "bob", "score": 90})\n'
                '    depot.put("c", {"name": "cyd", "score": 90})\n'
                '    depot.put("d", {"name": "dan", "score": 40})\n\n\n'
                "def test_top():\n"
                "    _seed()\n"
                '    assert [r["name"] for r in depot.top("score", 3)] == [\n'
                '        "bob", "cyd", "ann"\n'
                "    ]\n\n\n"
                "def test_top_tie_by_key():\n"
                "    _seed()\n"
                '    assert [r["name"] for r in depot.top("score", 2)] == ["bob", "cyd"]\n\n\n'
                "def test_page_regression():\n"
                "    _seed()\n"
                "    assert quota.PAGE_SIZE == 5\n"
                "    assert len(depot.page(0)) == 4\n"
            ),
            "ops": [("replace", "depot.py", _k8_old, _k8_new)],
            "expect_targets": {"depot.py"},
        },
        {
            "instruction": (
                "请修改 depot.py 中的 put：name 键存在时值还必须是非空白字符串"
                "（键缺失仍抛 ValueError）。"
            ),
            "tests": (
                "import pytest\n"
                "import depot\n\n\n"
                "def test_blank_name_rejected():\n"
                "    depot.ROWS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        depot.put("k", {"name": "   "})\n'
                "    with pytest.raises(ValueError):\n"
                '        depot.put("k2", {"name": ""})\n\n\n'
                "def test_missing_name_still_rejected():\n"
                "    depot.ROWS.clear()\n"
                "    with pytest.raises(ValueError):\n"
                '        depot.put("k", {"score": 1})\n\n\n'
                "def test_ok_name():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("k", {"name": " x "})\n'
                '    assert depot.get("k")["name"] == " x "\n\n\n'
                "def test_top_regression():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("a", {"name": "ann", "score": 5})\n'
                '    depot.put("b", {"name": "bob", "score": 9})\n'
                '    assert [r["name"] for r in depot.top("score", 1)] == ["bob"]\n'
            ),
            "ops": [("replace", "depot.py", _k9_old, _k9_new)],
            "expect_targets": {"depot.py"},
        },
        {
            "instruction": (
                "请修改 quota.py 中的 PAGE_SIZE：应从 5 改为 2，分页随之变小。"
            ),
            "tests": (
                "import quota\n"
                "import depot\n"
                "import api\n\n\n"
                "def test_page_size_revised():\n"
                "    assert quota.PAGE_SIZE == 2\n"
                "    depot.ROWS.clear()\n"
                "    for i in range(5):\n"
                '        depot.put(f"k{i}", {"name": f"n{i}"})\n'
                '    assert [r["name"] for r in depot.page(0)] == ["n0", "n1"]\n'
                '    assert [r["name"] for r in depot.page(1)] == ["n2", "n3"]\n\n\n'
                "def test_full_chain():\n"
                "    depot.ROWS.clear()\n"
                '    depot.put("a", {"name": "ann", "team": "red", "score": 70})\n'
                '    depot.put("b", {"name": "bob", "team": "red", "score": 90})\n'
                '    depot.put("c", {"name": "cyd", "team": "blue", "score": 40})\n'
                '    assert depot.get("a")["score"] == 70\n'
                '    assert [r["name"] for r in depot.where("team", "red")] == ["ann", "bob"]\n'
                '    assert api.count("team", "red") == 2\n'
                '    assert [r["name"] for r in depot.top("score", 2)] == ["bob", "ann"]\n'
                "    assert len(depot.page(0)) == 2\n"
            ),
            "ops": [("replace", "quota.py", "PAGE_SIZE = 5\n", "PAGE_SIZE = 2\n")],
            "expect_targets": {"quota.py"},
        },
    ],
    info_points=[
        {"id": "ip_get_default", "type": "interface",
         "value": "get(key, default=None) 缺失回退 default",
         "locator": "instruction:step1 + depot.py",
         "needed_by_steps": [1, 6, 10],
         "redundant_in_instruction": True},
        {"id": "ip_where_order", "type": "implementation",
         "value": "where 按 key 升序；top 按值降序、同值 key 升序",
         "locator": "instruction:step3 + instruction:step8",
         "needed_by_steps": [3, 4, 8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_page_size", "type": "critical_data",
         "value": "PAGE_SIZE：3→5（step7）→2（step10）",
         "locator": "instruction:step5 + instruction:step7 + instruction:step10",
         "needed_by_steps": [5, 7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_rows_keyed", "type": "history",
         "value": "ROWS 为 {key: rec} 字典，分页按 key 升序",
         "locator": "depot.py after step1 + assistant history",
         "needed_by_steps": [3, 5, 8],
         "redundant_in_instruction": False},
        {"id": "ip_name_constraint", "type": "history",
         "value": "put 的 name 约束：键存在（step6）→ 非空白（step9 改约）",
         "locator": "depot.py after step6 + instruction:step9",
         "needed_by_steps": [6, 9],
         "redundant_in_instruction": False},
    ],
)

# ============================================================ LF8 ind_long_plugin
# 变体 a：字典注册表（注册→分发→别名→钩子→全局策略）

_plg_a = (
    '"""Plugin registry."""\n\n\n'
    "HANDLERS = {}\n\n\n"
    "def register(name, fn):\n"
    "    HANDLERS[name] = fn\n"
)
_hks_a = (
    '"""Hook bus."""\n\n\n'
    "AFTER = []\n\n\n"
    "def on_after(fn):\n"
    "    AFTER.append(fn)\n"
)
_shl_a = (
    '"""Shell front."""\n\n\n'
    "def prompt():\n"
    '    return ">"\n'
)
_h1_old = "def register(name, fn):\n    HANDLERS[name] = fn"
_h1_new = _h1_old + "\n\n\ndef names():\n    return list(HANDLERS)"
_h2_old = "def names():\n    return list(HANDLERS)"
_h2_new = _h2_old + (
    "\n\n\ndef dispatch(name, *args):\n"
    "    fn = HANDLERS[name]\n"
    "    return fn(*args)"
)
_h3_old = _h1_old
_h3_new = (
    "def register(name, fn):\n"
    "    if name in HANDLERS:\n"
    '        raise ValueError("name")\n'
    "    HANDLERS[name] = fn"
)
_h4a_old = '"""Shell front."""'
_h4a_new = '"""Shell front."""\nimport plug'
_h4b_old = 'def prompt():\n    return ">"'
_h4b_new = _h4b_old + (
    "\n\n\ndef run(name, *args):\n"
    "    try:\n"
    "        return plug.dispatch(name, *args)\n"
    "    except KeyError:\n"
    '        return f"err:{name}"'
)
_h5a_old = "HANDLERS = {}"
_h5a_new = "HANDLERS = {}\nALIASES = {}"
_h5b_old = _h3_new
_h5b_new = _h3_new + (
    "\n\n\ndef alias(old, new):\n"
    "    if new not in HANDLERS:\n"
    "        raise KeyError(new)\n"
    "    ALIASES[old] = new"
)
_h5c_old = (
    "def dispatch(name, *args):\n"
    "    fn = HANDLERS[name]\n"
    "    return fn(*args)"
)
_h5c_new = (
    "def dispatch(name, *args):\n"
    "    if name in ALIASES:\n"
    "        name = ALIASES[name]\n"
    "    fn = HANDLERS[name]\n"
    "    return fn(*args)"
)
_h6a_old = '"""Plugin registry."""'
_h6a_new = '"""Plugin registry."""\nimport hooks'
_h6b_old = _h5c_new
_h6b_new = (
    "def dispatch(name, *args):\n"
    "    if name in ALIASES:\n"
    "        name = ALIASES[name]\n"
    "    fn = HANDLERS[name]\n"
    "    result = fn(*args)\n"
    "    for hook in hooks.AFTER:\n"
    "        hook(name, result)\n"
    "    return result"
)
_h7_old = "def on_after(fn):\n    AFTER.append(fn)"
_h7_new = _h7_old + (
    "\n\n\ndef clear():\n"
    "    n = len(AFTER)\n"
    "    AFTER.clear()\n"
    "    return n"
)
_h8a_old = (
    "def alias(old, new):\n"
    "    if new not in HANDLERS:\n"
    "        raise KeyError(new)\n"
    "    ALIASES[old] = new"
)
_h8a_new = (
    "def alias(old, new):\n"
    "    if new not in HANDLERS and new not in ALIASES:\n"
    "        raise KeyError(new)\n"
    "    ALIASES[old] = new"
)
_h8b_old = _h6b_new
_h8b_new = (
    "def dispatch(name, *args):\n"
    "    seen = 0\n"
    "    while name in ALIASES:\n"
    "        name = ALIASES[name]\n"
    "        seen += 1\n"
    "        if seen > 10:\n"
    '            raise ValueError("alias loop")\n'
    "    fn = HANDLERS[name]\n"
    "    result = fn(*args)\n"
    "    for hook in hooks.AFTER:\n"
    "        hook(name, result)\n"
    "    return result"
)
_h9a_old = "ALIASES = {}"
_h9a_new = "ALIASES = {}\nSTRICT = True"
_h9b_old = _h8b_new
_h9b_new = (
    "def dispatch(name, *args):\n"
    "    seen = 0\n"
    "    while name in ALIASES:\n"
    "        name = ALIASES[name]\n"
    "        seen += 1\n"
    "        if seen > 10:\n"
    '            raise ValueError("alias loop")\n'
    "    if name not in HANDLERS:\n"
    "        if STRICT:\n"
    "            raise KeyError(name)\n"
    "        return None\n"
    "    fn = HANDLERS[name]\n"
    "    result = fn(*args)\n"
    "    for hook in hooks.AFTER:\n"
    "        hook(name, result)\n"
    "    return result"
)
T(
    id="ind_L08a",
    family="ind_long_plugin",
    type="plugin_dispatch_evolution",
    difficulty="long",
    focus="10 步插件系统演进：注册→分发→去重→消费方→别名→钩子→链式别名→全局开关改约",
    files={"plug.py": _plg_a, "hooks.py": _hks_a, "shell.py": _shl_a},
    steps=[
        {
            "instruction": "plug.py 新增 names()：返回已注册名列表（按注册顺序）。",
            "tests": (
                "import plug\n\n\n"
                "def test_names_order():\n"
                "    plug.HANDLERS.clear()\n"
                '    plug.register("b", lambda: 2)\n'
                '    plug.register("a", lambda: 1)\n'
                '    assert plug.names() == ["b", "a"]\n\n\n'
                "def test_names_empty():\n"
                "    plug.HANDLERS.clear()\n"
                "    assert plug.names() == []\n\n\n"
                "def test_register_regression():\n"
                "    plug.HANDLERS.clear()\n"
                '    plug.register("x", lambda: 9)\n'
                '    assert "x" in plug.HANDLERS\n'
            ),
            "ops": [("replace", "plug.py", _h1_old, _h1_new)],
            "expect_targets": {"plug.py"},
        },
        {
            "instruction": (
                "plug.py 新增 dispatch(name, *args)：调用对应 handler 并返回结果，"
                "未注册名抛 KeyError。"
            ),
            "tests": (
                "import pytest\n"
                "import plug\n\n\n"
                "def test_dispatch():\n"
                "    plug.HANDLERS.clear()\n"
                '    plug.register("double", lambda x: x * 2)\n'
                '    assert plug.dispatch("double", 5) == 10\n\n\n'
                "def test_dispatch_missing():\n"
                "    plug.HANDLERS.clear()\n"
                "    with pytest.raises(KeyError):\n"
                '        plug.dispatch("nope")\n\n\n'
                "def test_names_regression():\n"
                "    plug.HANDLERS.clear()\n"
                '    plug.register("x", lambda: 1)\n'
                '    assert plug.names() == ["x"]\n'
            ),
            "ops": [("replace", "plug.py", _h2_old, _h2_new)],
            "expect_targets": {"plug.py"},
        },
        {
            "instruction": (
                "请修改 plug.py 中的 register：重复注册同名时抛 ValueError"
                "（首次注册行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import plug\n\n\n"
                "def test_duplicate_rejected():\n"
                "    plug.HANDLERS.clear()\n"
                '    plug.register("a", lambda: 1)\n'
                "    with pytest.raises(ValueError):\n"
                '        plug.register("a", lambda: 2)\n'
                '    assert plug.dispatch("a") == 1\n\n\n'
                "def test_new_name_ok():\n"
                "    plug.HANDLERS.clear()\n"
                '    plug.register("a", lambda: 1)\n'
                '    plug.register("b", lambda: 2)\n'
                '    assert plug.dispatch("b") == 2\n\n\n'
                "def test_dispatch_regression():\n"
                "    plug.HANDLERS.clear()\n"
                '    plug.register("double", lambda x: x * 2)\n'
                '    assert plug.dispatch("double", 5) == 10\n'
            ),
            "ops": [("replace", "plug.py", _h3_old, _h3_new)],
            "expect_targets": {"plug.py"},
        },
        {
            "instruction": (
                "shell.py 新增 run(name, *args)：调用 plug.py 的 dispatch，"
                "捕获 KeyError 并返回 'err:name'（需要补充 import）。"
            ),
            "tests": (
                "import plug\n"
                "import shell\n\n\n"
                "def test_run_ok():\n"
                "    plug.HANDLERS.clear()\n"
                '    plug.register("echo", lambda x: f"got:{x}")\n'
                '    assert shell.run("echo", "hi") == "got:hi"\n\n\n'
                "def test_run_missing():\n"
                "    plug.HANDLERS.clear()\n"
                '    assert shell.run("nope") == "err:nope"\n\n\n'
                "def test_prompt_regression():\n"
                '    assert shell.prompt() == ">"\n\n\n'
                "def test_names_regression():\n"
                "    plug.HANDLERS.clear()\n"
                '    plug.register("x", lambda: 1)\n'
                '    assert plug.names() == ["x"]\n'
            ),
            "ops": [
                ("replace", "shell.py", _h4a_old, _h4a_new),
                ("replace", "shell.py", _h4b_old, _h4b_new),
            ],
            "expect_targets": {"shell.py", "plug.py"},
        },
        {
            "instruction": (
                "plug.py 新增 alias(old, new)：把 old 注册为 new 的别名"
                "（new 必须已注册，否则 KeyError），dispatch 解析别名后执行。"
            ),
            "tests": (
                "import pytest\n"
                "import plug\n"
                "import shell\n\n\n"
                "def _seed():\n"
                "    plug.HANDLERS.clear()\n"
                "    plug.ALIASES.clear()\n"
                '    plug.register("greet", lambda: "hi")\n\n\n'
                "def test_alias_dispatch():\n"
                "    _seed()\n"
                '    plug.alias("hi", "greet")\n'
                '    assert plug.dispatch("hi") == "hi"\n\n\n'
                "def test_alias_target_missing():\n"
                "    _seed()\n"
                "    with pytest.raises(KeyError):\n"
                '        plug.alias("x", "ghost")\n\n\n'
                "def test_shell_regression():\n"
                "    _seed()\n"
                '    assert shell.run("greet") == "hi"\n'
            ),
            "ops": [
                ("replace", "plug.py", _h5a_old, _h5a_new),
                ("replace", "plug.py", _h5b_old, _h5b_new),
                ("replace", "plug.py", _h5c_old, _h5c_new),
            ],
            "expect_targets": {"plug.py"},
        },
        {
            "instruction": (
                "请修改 plug.py 中的 dispatch：在 handler 执行后应依次调用 hooks 模块的 "
                "AFTER 钩子（传 name 与结果）（需要补充 import）。"
            ),
            "tests": (
                "import plug\n"
                "import hooks\n\n\n"
                "def _seed():\n"
                "    plug.HANDLERS.clear()\n"
                "    plug.ALIASES.clear()\n"
                "    hooks.AFTER.clear()\n"
                '    plug.register("echo", lambda x: x * 3)\n\n\n'
                "def test_hooks_called():\n"
                "    _seed()\n"
                "    seen = []\n"
                "    hooks.on_after(lambda name, result: seen.append((name, result)))\n"
                '    assert plug.dispatch("echo", 4) == 12\n'
                '    assert seen == [("echo", 12)]\n\n\n'
                "def test_no_hooks():\n"
                "    _seed()\n"
                '    assert plug.dispatch("echo", 1) == 3\n\n\n'
                "def test_alias_regression():\n"
                "    _seed()\n"
                '    plug.alias("e", "echo")\n'
                '    assert plug.dispatch("e", 2) == 6\n'
            ),
            "ops": [
                ("replace", "plug.py", _h6a_old, _h6a_new),
                ("replace", "plug.py", _h6b_old, _h6b_new),
            ],
            "expect_targets": {"plug.py"},
        },
        {
            "instruction": (
                "hooks.py 新增 clear()：清空 AFTER 并返回清空前的条数。"
            ),
            "tests": (
                "import hooks\n"
                "import plug\n\n\n"
                "def test_clear():\n"
                "    hooks.AFTER.clear()\n"
                "    hooks.on_after(lambda n, r: None)\n"
                "    hooks.on_after(lambda n, r: None)\n"
                "    assert hooks.clear() == 2\n"
                "    assert hooks.AFTER == []\n\n\n"
                "def test_clear_empty():\n"
                "    hooks.AFTER.clear()\n"
                "    assert hooks.clear() == 0\n\n\n"
                "def test_hook_dispatch_regression():\n"
                "    plug.HANDLERS.clear()\n"
                "    plug.ALIASES.clear()\n"
                "    hooks.AFTER.clear()\n"
                '    plug.register("echo", lambda x: x + 1)\n'
                "    seen = []\n"
                "    hooks.on_after(lambda n, r: seen.append(r))\n"
                '    plug.dispatch("echo", 1)\n'
                "    assert seen == [2]\n"
            ),
            "ops": [("replace", "hooks.py", _h7_old, _h7_new)],
            "expect_targets": {"hooks.py"},
        },
        {
            "instruction": (
                "请修改 plug.py 中的 alias 与 dispatch：alias 的 new 可以指向别名"
                "（允许链式），dispatch 循环解析别名（超过 10 层视为环抛 ValueError）。"
            ),
            "tests": (
                "import pytest\n"
                "import plug\n"
                "import hooks\n\n\n"
                "def _seed():\n"
                "    plug.HANDLERS.clear()\n"
                "    plug.ALIASES.clear()\n"
                "    hooks.AFTER.clear()\n"
                '    plug.register("real", lambda: "ok")\n\n\n'
                "def test_alias_chain():\n"
                "    _seed()\n"
                '    plug.alias("a", "real")\n'
                '    plug.alias("b", "a")\n'
                '    assert plug.dispatch("b") == "ok"\n\n\n'
                "def test_alias_loop():\n"
                "    _seed()\n"
                '    plug.register("r", lambda: 1)\n'
                '    plug.alias("p", "r")\n'
                '    plug.alias("q", "p")\n'
                '    plug.alias("p", "q")\n'
                "    with pytest.raises(ValueError):\n"
                '        plug.dispatch("p")\n\n\n'
                "def test_single_alias_regression():\n"
                "    _seed()\n"
                '    plug.alias("s", "real")\n'
                '    assert plug.dispatch("s") == "ok"\n'
            ),
            "ops": [
                ("replace", "plug.py", _h8a_old, _h8a_new),
                ("replace", "plug.py", _h8b_old, _h8b_new),
            ],
            "expect_targets": {"plug.py"},
        },
        {
            "instruction": (
                "plug.py 新增 STRICT = True：全局开关——为 True 时 dispatch 未注册名"
                "抛 KeyError，为 False 时返回 None。"
            ),
            "tests": (
                "import pytest\n"
                "import plug\n"
                "import hooks\n\n\n"
                "def _seed():\n"
                "    plug.HANDLERS.clear()\n"
                "    plug.ALIASES.clear()\n"
                "    hooks.AFTER.clear()\n\n\n"
                "def test_strict_true():\n"
                "    _seed()\n"
                "    assert plug.STRICT is True\n"
                "    with pytest.raises(KeyError):\n"
                '        plug.dispatch("missing")\n\n\n'
                "def test_strict_false():\n"
                "    _seed()\n"
                "    plug.STRICT = False\n"
                "    assert plug.dispatch(\"missing\") is None\n\n\n"
                "def test_registered_still_works():\n"
                "    _seed()\n"
                '    plug.register("r", lambda: 5)\n'
                '    assert plug.dispatch("r") == 5\n'
            ),
            "ops": [
                ("replace", "plug.py", _h9a_old, _h9a_new),
                ("replace", "plug.py", _h9b_old, _h9b_new),
            ],
            "expect_targets": {"plug.py"},
        },
        {
            "instruction": (
                "请修改 plug.py 中的 STRICT：默认应改为 False（未注册名分发返回 None）。"
            ),
            "tests": (
                "import pytest\n"
                "import plug\n"
                "import hooks\n"
                "import shell\n\n\n"
                "def _seed():\n"
                "    plug.HANDLERS.clear()\n"
                "    plug.ALIASES.clear()\n"
                "    hooks.AFTER.clear()\n\n\n"
                "def test_strict_default_false():\n"
                "    _seed()\n"
                "    assert plug.STRICT is False\n"
                '    assert plug.dispatch("missing") is None\n\n\n'
                "def test_strict_override():\n"
                "    _seed()\n"
                "    plug.STRICT = True\n"
                "    with pytest.raises(KeyError):\n"
                '        plug.dispatch("missing")\n\n\n'
                "def test_full_chain():\n"
                "    _seed()\n"
                "    plug.STRICT = False\n"
                '    plug.register("greet", lambda n: f"hi {n}")\n'
                '    plug.alias("hi", "greet")\n'
                "    seen = []\n"
                "    hooks.on_after(lambda name, result: seen.append((name, result)))\n"
                '    assert plug.dispatch("hi", "bob") == "hi bob"\n'
                '    assert seen == [("greet", "hi bob")]\n'
                '    assert plug.names() == ["greet"]\n'
                '    assert shell.run("ghost") is None\n'
            ),
            "ops": [("replace", "plug.py", "STRICT = True\n", "STRICT = False\n")],
            "expect_targets": {"plug.py"},
        },
    ],
    info_points=[
        {"id": "ip_dispatch_contract", "type": "interface",
         "value": "dispatch 调用 handler 并返回结果",
         "locator": "instruction:step2 + plug.py",
         "needed_by_steps": [2, 4, 9, 10],
         "redundant_in_instruction": True},
        {"id": "ip_alias_rules", "type": "implementation",
         "value": "alias 指向已注册名；step8 起允许链式并限 10 层",
         "locator": "instruction:step5 + instruction:step8",
         "needed_by_steps": [5, 8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_hook_bus", "type": "implementation",
         "value": "AFTER 钩子在 handler 后执行，参数 (name, result)",
         "locator": "instruction:step6 + plug.py",
         "needed_by_steps": [6, 7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_handlers_shape", "type": "history",
         "value": "HANDLERS/ALIASES 为字典，names 按注册顺序",
         "locator": "plug.py after step1 + assistant history",
         "needed_by_steps": [1, 3, 5],
         "redundant_in_instruction": False},
        {"id": "ip_strict_policy", "type": "critical_data",
         "value": "STRICT：True（step9）→False（step10）",
         "locator": "instruction:step9 + instruction:step10",
         "needed_by_steps": [9, 10],
         "redundant_in_instruction": True},
    ],
)

# 变体 b：优先级列表面板（注册→分发→别名→before 钩子→静默策略）

_pan_b = (
    '"""Priority panel."""\n\n\n'
    "PLUGINS = []\n\n\n"
    "def plug(name, fn):\n"
    "    PLUGINS.append((name, fn))\n"
)
_pre_b = (
    '"""Before hooks."""\n\n\n'
    "BEFORE = []\n\n\n"
    "def on_before(fn):\n"
    "    BEFORE.append(fn)\n"
)
_cli_b = (
    '"""Cli front."""\n\n\n'
    "def banner():\n"
    '    return "cli"\n'
)
_q1_old = "def plug(name, fn):\n    PLUGINS.append((name, fn))"
_q1_new = _q1_old + "\n\n\ndef count():\n    return len(PLUGINS)"
_q2_old = "def count():\n    return len(PLUGINS)"
_q2_new = _q2_old + (
    "\n\n\ndef run(name, *args):\n"
    "    for pname, fn in PLUGINS:\n"
    "        if pname == name:\n"
    "            return fn(*args)\n"
    "    raise KeyError(name)"
)
_q3_old = _q1_old
_q3_new = (
    "def plug(name, fn):\n"
    "    if any(p[0] == name for p in PLUGINS):\n"
    '        raise ValueError("name")\n'
    "    PLUGINS.append((name, fn))"
)
_q4a_old = '"""Cli front."""'
_q4a_new = '"""Cli front."""\nimport panel'
_q4b_old = 'def banner():\n    return "cli"'
_q4b_new = _q4b_old + (
    "\n\n\ndef call(name, *args):\n"
    "    try:\n"
    "        return panel.run(name, *args)\n"
    "    except KeyError:\n"
    "        return None"
)
_q5a_old = "PLUGINS = []"
_q5a_new = "PLUGINS = []\nALIASES = {}"
_q5b_old = _q3_new
_q5b_new = _q3_new + (
    "\n\n\ndef alias(old, new):\n"
    "    if new not in {p[0] for p in PLUGINS}:\n"
    "        raise KeyError(new)\n"
    "    ALIASES[old] = new"
)
_q5c_old = (
    "def run(name, *args):\n"
    "    for pname, fn in PLUGINS:\n"
    "        if pname == name:\n"
    "            return fn(*args)\n"
    "    raise KeyError(name)"
)
_q5c_new = (
    "def run(name, *args):\n"
    "    name = ALIASES.get(name, name)\n"
    "    for pname, fn in PLUGINS:\n"
    "        if pname == name:\n"
    "            return fn(*args)\n"
    "    raise KeyError(name)"
)
_q6a_old = '"""Priority panel."""'
_q6a_new = '"""Priority panel."""\nimport pre'
_q6b_old = _q5c_new
_q6b_new = (
    "def run(name, *args):\n"
    "    name = ALIASES.get(name, name)\n"
    "    for hook in pre.BEFORE:\n"
    "        hook(name)\n"
    "    for pname, fn in PLUGINS:\n"
    "        if pname == name:\n"
    "            return fn(*args)\n"
    "    raise KeyError(name)"
)
_q7a_old = _q3_new
_q7a_new = (
    "def plug(name, fn, prio=0):\n"
    "    if any(p[0] == name for p in PLUGINS):\n"
    '        raise ValueError("name")\n'
    "    PLUGINS.append((name, fn, prio))"
)
_q7b_old = _q6b_new
_q7b_new = (
    "def run(name, *args):\n"
    "    name = ALIASES.get(name, name)\n"
    "    for hook in pre.BEFORE:\n"
    "        hook(name)\n"
    "    for pname, fn, _prio in PLUGINS:\n"
    "        if pname == name:\n"
    "            return fn(*args)\n"
    "    raise KeyError(name)\n\n\n"
    "def run_all(*args):\n"
    "    ordered = sorted(PLUGINS, key=lambda p: -p[2])\n"
    "    return [fn(*args) for _n, fn, _p in ordered]"
)
_q8a_old = "ALIASES = {}"
_q8a_new = "ALIASES = {}\nSILENT = False"
_q8b_old = (
    "def run(name, *args):\n"
    "    name = ALIASES.get(name, name)\n"
    "    for hook in pre.BEFORE:\n"
    "        hook(name)\n"
    "    for pname, fn, _prio in PLUGINS:\n"
    "        if pname == name:\n"
    "            return fn(*args)\n"
    "    raise KeyError(name)"
)
_q8b_new = (
    "def run(name, *args):\n"
    "    name = ALIASES.get(name, name)\n"
    "    for hook in pre.BEFORE:\n"
    "        hook(name)\n"
    "    for pname, fn, _prio in PLUGINS:\n"
    "        if pname == name:\n"
    "            return fn(*args)\n"
    "    if SILENT:\n"
    "        return None\n"
    "    raise KeyError(name)"
)
_q9_old = _q8b_new
_q9_new = (
    "def run(name, *args):\n"
    "    name = ALIASES.get(name, name)\n"
    "    for hook in pre.BEFORE:\n"
    "        if hook(name) is False:\n"
    "            return None\n"
    "    for pname, fn, _prio in PLUGINS:\n"
    "        if pname == name:\n"
    "            return fn(*args)\n"
    "    if SILENT:\n"
    "        return None\n"
    "    raise KeyError(name)"
)
T(
    id="ind_L08b",
    family="ind_long_plugin",
    type="plugin_dispatch_evolution",
    difficulty="long",
    focus="10 步优先级面板演进：计数→分发→去重→消费方→别名→before 钩子→优先级→静默改约",
    files={"panel.py": _pan_b, "pre.py": _pre_b, "cli.py": _cli_b},
    steps=[
        {
            "instruction": "panel.py 新增 count()：返回 PLUGINS 中的插件条数。",
            "tests": (
                "import panel\n\n\n"
                "def test_count():\n"
                "    panel.PLUGINS.clear()\n"
                '    panel.plug("a", lambda: 1)\n'
                '    panel.plug("b", lambda: 2)\n'
                "    assert panel.count() == 2\n\n\n"
                "def test_count_empty():\n"
                "    panel.PLUGINS.clear()\n"
                "    assert panel.count() == 0\n\n\n"
                "def test_plug_regression():\n"
                "    panel.PLUGINS.clear()\n"
                '    panel.plug("a", lambda: 1)\n'
                "    assert len(panel.PLUGINS) == 1\n"
            ),
            "ops": [("replace", "panel.py", _q1_old, _q1_new)],
            "expect_targets": {"panel.py"},
        },
        {
            "instruction": (
                "panel.py 新增 run(name, *args)：按注册顺序找到首个同名插件执行"
                "并返回结果，未找到抛 KeyError。"
            ),
            "tests": (
                "import pytest\n"
                "import panel\n\n\n"
                "def test_run():\n"
                "    panel.PLUGINS.clear()\n"
                '    panel.plug("double", lambda x: x * 2)\n'
                '    assert panel.run("double", 5) == 10\n\n\n'
                "def test_run_missing():\n"
                "    panel.PLUGINS.clear()\n"
                "    with pytest.raises(KeyError):\n"
                '        panel.run("nope")\n\n\n'
                "def test_count_regression():\n"
                "    panel.PLUGINS.clear()\n"
                '    panel.plug("a", lambda: 1)\n'
                "    assert panel.count() == 1\n"
            ),
            "ops": [("replace", "panel.py", _q2_old, _q2_new)],
            "expect_targets": {"panel.py"},
        },
        {
            "instruction": (
                "请修改 panel.py 中的 plug：重复注册同名插件时抛 ValueError"
                "（首次注册行为不变）。"
            ),
            "tests": (
                "import pytest\n"
                "import panel\n\n\n"
                "def test_duplicate_rejected():\n"
                "    panel.PLUGINS.clear()\n"
                '    panel.plug("a", lambda: 1)\n'
                "    with pytest.raises(ValueError):\n"
                '        panel.plug("a", lambda: 2)\n'
                '    assert panel.run("a") == 1\n\n\n'
                "def test_new_name_ok():\n"
                "    panel.PLUGINS.clear()\n"
                '    panel.plug("a", lambda: 1)\n'
                '    panel.plug("b", lambda: 2)\n'
                '    assert panel.run("b") == 2\n\n\n'
                "def test_run_regression():\n"
                "    panel.PLUGINS.clear()\n"
                '    panel.plug("double", lambda x: x * 2)\n'
                '    assert panel.run("double", 5) == 10\n'
            ),
            "ops": [("replace", "panel.py", _q3_old, _q3_new)],
            "expect_targets": {"panel.py"},
        },
        {
            "instruction": (
                "cli.py 新增 call(name, *args)：调用 panel.py 的 run，"
                "捕获 KeyError 并返回 None（需要补充 import）。"
            ),
            "tests": (
                "import panel\n"
                "import cli\n\n\n"
                "def test_call_ok():\n"
                "    panel.PLUGINS.clear()\n"
                '    panel.plug("echo", lambda x: f"got:{x}")\n'
                '    assert cli.call("echo", "hi") == "got:hi"\n\n\n'
                "def test_call_missing():\n"
                "    panel.PLUGINS.clear()\n"
                '    assert cli.call("nope") is None\n\n\n'
                "def test_banner_regression():\n"
                '    assert cli.banner() == "cli"\n\n\n'
                "def test_count_regression():\n"
                "    panel.PLUGINS.clear()\n"
                '    panel.plug("a", lambda: 1)\n'
                "    assert panel.count() == 1\n"
            ),
            "ops": [
                ("replace", "cli.py", _q4a_old, _q4a_new),
                ("replace", "cli.py", _q4b_old, _q4b_new),
            ],
            "expect_targets": {"cli.py", "panel.py"},
        },
        {
            "instruction": (
                "panel.py 新增 alias(old, new)：把 old 注册为 new 的别名"
                "（new 必须已注册，否则 KeyError），run 解析别名后执行。"
            ),
            "tests": (
                "import pytest\n"
                "import panel\n"
                "import cli\n\n\n"
                "def _seed():\n"
                "    panel.PLUGINS.clear()\n"
                "    panel.ALIASES.clear()\n"
                '    panel.plug("greet", lambda: "hi")\n\n\n'
                "def test_alias_run():\n"
                "    _seed()\n"
                '    panel.alias("hi", "greet")\n'
                '    assert panel.run("hi") == "hi"\n\n\n'
                "def test_alias_target_missing():\n"
                "    _seed()\n"
                "    with pytest.raises(KeyError):\n"
                '        panel.alias("x", "ghost")\n\n\n'
                "def test_call_regression():\n"
                "    _seed()\n"
                '    assert cli.call("greet") == "hi"\n'
            ),
            "ops": [
                ("replace", "panel.py", _q5a_old, _q5a_new),
                ("replace", "panel.py", _q5b_old, _q5b_new),
                ("replace", "panel.py", _q5c_old, _q5c_new),
            ],
            "expect_targets": {"panel.py"},
        },
        {
            "instruction": (
                "请修改 panel.py 中的 run：执行 handler 前依次调用 pre 模块的 "
                "BEFORE 钩子（需要补充 import）。"
            ),
            "tests": (
                "import panel\n"
                "import pre\n\n\n"
                "def _seed():\n"
                "    panel.PLUGINS.clear()\n"
                "    panel.ALIASES.clear()\n"
                "    pre.BEFORE.clear()\n"
                '    panel.plug("echo", lambda x: x * 3)\n\n\n'
                "def test_before_hooks():\n"
                "    _seed()\n"
                "    seen = []\n"
                "    pre.on_before(lambda name: seen.append(name))\n"
                '    assert panel.run("echo", 4) == 12\n'
                '    assert seen == ["echo"]\n\n\n'
                "def test_no_hooks():\n"
                "    _seed()\n"
                '    assert panel.run("echo", 2) == 6\n\n\n'
                "def test_alias_regression():\n"
                "    _seed()\n"
                '    panel.alias("e", "echo")\n'
                '    assert panel.run("e", 1) == 3\n'
            ),
            "ops": [
                ("replace", "panel.py", _q6a_old, _q6a_new),
                ("replace", "panel.py", _q6b_old, _q6b_new),
            ],
            "expect_targets": {"panel.py"},
        },
        {
            "instruction": (
                "请修改 panel.py 中的 plug：签名改为 plug(name, fn, prio=0) 并存入优先级；"
                "并新增 run_all(*args)：按优先级降序执行全部插件返回结果列表"
                "（同优先级按注册顺序）。"
            ),
            "tests": (
                "import pytest\n"
                "import panel\n"
                "import pre\n\n\n"
                "def _seed():\n"
                "    panel.PLUGINS.clear()\n"
                "    panel.ALIASES.clear()\n"
                "    pre.BEFORE.clear()\n\n\n"
                "def test_run_all_priority():\n"
                "    _seed()\n"
                '    panel.plug("a", lambda: "A", prio=1)\n'
                '    panel.plug("b", lambda: "B", prio=5)\n'
                '    panel.plug("c", lambda: "C", prio=5)\n'
                '    assert panel.run_all() == ["B", "C", "A"]\n\n\n'
                "def test_run_still_works():\n"
                "    _seed()\n"
                '    panel.plug("x", lambda v: v + 1, prio=3)\n'
                '    assert panel.run("x", 4) == 5\n\n\n'
                "def test_duplicate_still_rejected():\n"
                "    _seed()\n"
                '    panel.plug("a", lambda: 1)\n'
                "    with pytest.raises(ValueError):\n"
                '        panel.plug("a", lambda: 2)\n\n\n'
                "def test_before_regression():\n"
                "    _seed()\n"
                "    seen = []\n"
                "    pre.on_before(lambda name: seen.append(name))\n"
                '    panel.plug("echo", lambda: 5)\n'
                '    panel.run("echo")\n'
                '    assert seen == ["echo"]\n'
            ),
            "ops": [
                ("replace", "panel.py", _q7a_old, _q7a_new),
                ("replace", "panel.py", _q7b_old, _q7b_new),
            ],
            "expect_targets": {"panel.py"},
        },
        {
            "instruction": (
                "panel.py 新增 SILENT = False：全局开关——为 True 时 run 未找到插件"
                "返回 None，为 False 时抛 KeyError。"
            ),
            "tests": (
                "import pytest\n"
                "import panel\n"
                "import pre\n\n\n"
                "def _seed():\n"
                "    panel.PLUGINS.clear()\n"
                "    panel.ALIASES.clear()\n"
                "    pre.BEFORE.clear()\n\n\n"
                "def test_silent_false_default():\n"
                "    _seed()\n"
                "    assert panel.SILENT is False\n"
                "    with pytest.raises(KeyError):\n"
                '        panel.run("missing")\n\n\n'
                "def test_silent_true():\n"
                "    _seed()\n"
                "    panel.SILENT = True\n"
                '    assert panel.run("missing") is None\n\n\n'
                "def test_registered_works():\n"
                "    _seed()\n"
                '    panel.plug("r", lambda: 5)\n'
                '    assert panel.run("r") == 5\n'
            ),
            "ops": [
                ("replace", "panel.py", _q8a_old, _q8a_new),
                ("replace", "panel.py", _q8b_old, _q8b_new),
            ],
            "expect_targets": {"panel.py"},
        },
        {
            "instruction": (
                "请修改 panel.py 中的 run：BEFORE 钩子返回 False 时应中止执行并返回 None"
                "（返回其他值继续执行）。"
            ),
            "tests": (
                "import panel\n"
                "import pre\n\n\n"
                "def _seed():\n"
                "    panel.PLUGINS.clear()\n"
                "    panel.ALIASES.clear()\n"
                "    pre.BEFORE.clear()\n"
                '    panel.plug("danger", lambda: "ran")\n\n\n'
                "def test_hook_blocks():\n"
                "    _seed()\n"
                "    pre.on_before(lambda name: False)\n"
                '    assert panel.run("danger") is None\n\n\n'
                "def test_hook_pass():\n"
                "    _seed()\n"
                "    pre.on_before(lambda name: True)\n"
                '    assert panel.run("danger") == "ran"\n\n\n'
                "def test_silent_regression():\n"
                "    _seed()\n"
                "    panel.SILENT = True\n"
                '    assert panel.run("missing") is None\n'
            ),
            "ops": [("replace", "panel.py", _q9_old, _q9_new)],
            "expect_targets": {"panel.py"},
        },
        {
            "instruction": (
                "请修改 panel.py 中的 SILENT：默认应改为 True（未知名分发返回 None）。"
            ),
            "tests": (
                "import pytest\n"
                "import panel\n"
                "import pre\n"
                "import cli\n\n\n"
                "def _seed():\n"
                "    panel.PLUGINS.clear()\n"
                "    panel.ALIASES.clear()\n"
                "    pre.BEFORE.clear()\n\n\n"
                "def test_silent_default_true():\n"
                "    _seed()\n"
                "    assert panel.SILENT is True\n"
                '    assert panel.run("missing") is None\n\n\n'
                "def test_strict_override():\n"
                "    _seed()\n"
                "    panel.SILENT = False\n"
                "    with pytest.raises(KeyError):\n"
                '        panel.run("missing")\n\n\n'
                "def test_full_chain():\n"
                "    _seed()\n"
                '    panel.plug("greet", lambda n: f"hi {n}", prio=2)\n'
                '    panel.plug("bye", lambda n: f"by {n}", prio=9)\n'
                '    panel.alias("hey", "greet")\n'
                "    seen = []\n"
                "    pre.on_before(lambda name: seen.append(name))\n"
                '    assert panel.run("hey", "bob") == "hi bob"\n'
                '    assert seen == ["greet"]\n'
                '    assert panel.run_all("z") == ["by z", "hi z"]\n'
                '    assert cli.call("ghost") is None\n'
                "    assert panel.count() == 2\n"
            ),
            "ops": [("replace", "panel.py", "SILENT = False\n", "SILENT = True\n")],
            "expect_targets": {"panel.py"},
        },
    ],
    info_points=[
        {"id": "ip_run_contract", "type": "interface",
         "value": "run 按注册序执行首个同名插件；未知名 KeyError→SILENT 时 None",
         "locator": "instruction:step2 + instruction:step8",
         "needed_by_steps": [2, 4, 8, 10],
         "redundant_in_instruction": True},
        {"id": "ip_prio_order", "type": "implementation",
         "value": "plug(name, fn, prio=0)；run_all 按 prio 降序稳定排序",
         "locator": "instruction:step7 + panel.py",
         "needed_by_steps": [7, 10],
         "redundant_in_instruction": True},
        {"id": "ip_hook_before", "type": "implementation",
         "value": "BEFORE 在执行前调用；step9 起返回 False 中止",
         "locator": "instruction:step6 + instruction:step9",
         "needed_by_steps": [6, 9, 10],
         "redundant_in_instruction": True},
        {"id": "ip_plugins_shape", "type": "history",
         "value": "PLUGINS 为 (name, fn[, prio]) 元组列表",
         "locator": "panel.py after step1 + assistant history",
         "needed_by_steps": [1, 3, 5, 7],
         "redundant_in_instruction": False},
        {"id": "ip_silent_policy", "type": "critical_data",
         "value": "SILENT：False（step8）→True（step10）",
         "locator": "instruction:step8 + instruction:step10",
         "needed_by_steps": [8, 10],
         "redundant_in_instruction": True},
    ],
)
