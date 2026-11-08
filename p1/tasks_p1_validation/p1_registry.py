"""P1 任务注册表（共享单例，避免 __main__ 双导入分裂）。"""

TASKS: list = []


def T(**kw):
    assert "info_points" in kw, f"{kw.get('id')}: missing info_points (CMR 预声明)"
    TASKS.append(kw)
