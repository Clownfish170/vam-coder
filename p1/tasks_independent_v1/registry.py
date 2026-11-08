"""独立任务集注册表（Part2 independent-v1）（共享单例，避免 __main__ 双导入分裂）。"""

TASKS: list = []


def T(**kw):
    assert "info_points" in kw, f"{kw.get('id')}: missing info_points (CMR 预声明)"
    TASKS.append(kw)
