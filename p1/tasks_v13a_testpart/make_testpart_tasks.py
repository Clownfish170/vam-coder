#!/usr/bin/env python
"""生成 V13A_testpart 任务：6 个筛选题 + 2 个 extract 取值题。

extract 题用于区分 ICG（强制 FULL 相关取值文件）vs CR-skip（跳过可能丢数值）。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # p1/
SCREEN = ROOT / "tasks_v13a_screen"
OUT = ROOT / "tasks_v13a_testpart"


def _write(base: Path, files: dict[str, str]) -> None:
    if base.exists():
        shutil.rmtree(base)
    for rel, body in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


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


def make_extract_tasks() -> list[dict]:
    # sc07: 必须看到 cfg 中 LIMIT 才能写死 42
    sc07 = {
        "id": "sc07_extract",
        "project": {
            "cfg.py": "LIMIT = 42\nNAME = 'sc07'\n",
            "app.py": "def get():\n    return 0\n",
            "noise.py": "def noise():\n    return -1\n",
        },
        "steps": [
            {
                "id": "step1",
                "instruction": "请读取 cfg.py 中的 LIMIT 值。写死到 app.py 的 get()，返回该常量数值（不要写符号名）。不要修改 cfg.py。",
                "eval": "eval/step1",
            },
            {
                "id": "step2",
                "instruction": "请读取 cfg.py 中的 LIMIT。写死到 app.py 的 get()：返回该数值减 2。不要修改 cfg.py。",
                "eval": "eval/step2",
            },
            {
                "id": "step3",
                "instruction": "请在 app.py 新增 double_get() 返回 get() * 2。不要修改 cfg.py 与 noise.py。",
                "eval": "eval/step3",
            },
            {
                "id": "step4",
                "instruction": "请读取 cfg.py 中的 LIMIT。写死到 app.py 的 get()：返回该数值加 0。不要修改 cfg.py。",
                "eval": "eval/step4",
            },
            {
                "id": "step5",
                "instruction": "请修改 app.py 中的 double_get()：返回 get() + get()。不要修改 cfg.py。",
                "eval": "eval/step5",
            },
        ],
        "_refs": {
            "step1": {"app.py": "def get():\n    return 42\n"},
            "step2": {"app.py": "def get():\n    return 40\n"},
            "step3": {
                "app.py": (
                    "def get():\n    return 40\n\n\n"
                    "def double_get():\n    return get() * 2\n"
                )
            },
            "step4": {"app.py": "def get():\n    return 42\n"},
            "step5": {
                "app.py": (
                    "def get():\n    return 42\n\n\n"
                    "def double_get():\n    return get() + get()\n"
                )
            },
        },
        "_evals": {
            "step1": "def test():\n    from app import get\n    assert get() == 42\n",
            "step2": "def test():\n    from app import get\n    assert get() == 40\n",
            "step3": "def test():\n    from app import double_get\n    assert double_get() == 80\n",
            "step4": "def test():\n    from app import get\n    assert get() == 42\n",
            "step5": "def test():\n    from app import double_get\n    assert double_get() == 84\n",
        },
    }
    # sc08: 取值 + 无关噪声
    sc08 = {
        "id": "sc08_extract_noise",
        "project": {
            "tax.py": "RATE = 0.25\nTAG = 'sc08'\n",
            "bill.py": "def total(x):\n    return x\n",
            "junk.py": "def junk():\n    return 999\n",
        },
        "steps": [
            {
                "id": "step1",
                "instruction": "请读取 tax.py 中的 RATE 值。写死到 bill.py 的 total(x)，返回 x 乘以该数值。不要修改 tax.py。",
                "eval": "eval/step1",
            },
            {
                "id": "step2",
                "instruction": "请读取 tax.py 中的 RATE。写死到 bill.py 的 total(x)：返回 x 乘以该数值再加 1。不要修改 tax.py。",
                "eval": "eval/step2",
            },
            {
                "id": "step3",
                "instruction": "请在 bill.py 新增 fee(x) 返回 total(x) * 2。不要修改 tax.py 与 junk.py。",
                "eval": "eval/step3",
            },
            {
                "id": "step4",
                "instruction": "请修改 bill.py 中的 fee(x)：返回 total(x) + 1。不要修改 tax.py。",
                "eval": "eval/step4",
            },
            {
                "id": "step5",
                "instruction": "请修改 bill.py 中的 total(x)：写死为 x * 0.5。不要修改 tax.py。",
                "eval": "eval/step5",
            },
        ],
        "_refs": {
            "step1": {"bill.py": "def total(x):\n    return x * 0.25\n"},
            "step2": {"bill.py": "def total(x):\n    return x * 0.25 + 1\n"},
            "step3": {
                "bill.py": (
                    "def total(x):\n    return x * 0.25 + 1\n\n\n"
                    "def fee(x):\n    return total(x) * 2\n"
                )
            },
            "step4": {
                "bill.py": (
                    "def total(x):\n    return x * 0.25 + 1\n\n\n"
                    "def fee(x):\n    return total(x) + 1\n"
                )
            },
            "step5": {
                "bill.py": (
                    "def total(x):\n    return x * 0.5\n\n\n"
                    "def fee(x):\n    return total(x) + 1\n"
                )
            },
        },
        "_evals": {
            "step1": "def test():\n    from bill import total\n    assert abs(total(4) - 1.0) < 1e-9\n",
            "step2": "def test():\n    from bill import total\n    assert abs(total(4) - 2.0) < 1e-9\n",
            "step3": "def test():\n    from bill import fee\n    assert abs(fee(4) - 4.0) < 1e-9\n",
            "step4": "def test():\n    from bill import fee\n    assert abs(fee(4) - 3.0) < 1e-9\n",
            "step5": "def test():\n    from bill import total\n    assert abs(total(8) - 4.0) < 1e-9\n    assert abs(total(4) - 2.0) < 1e-9\n",
        },
    }
    return [sc07, sc08]


def _cumulative_pack(ep: dict) -> dict:
    tid = ep["id"]
    steps = ep["steps"]
    project = ep["project"]
    refs = ep["_refs"]
    evals = ep["_evals"]
    _write(OUT / tid / "project", project)
    state = dict(project)
    for step in steps:
        sid = step["id"]
        state = dict(state)
        state.update(refs[sid])
        _write(OUT / tid / "reference" / sid, state)
        ev = OUT / tid / "eval" / sid
        ev.mkdir(parents=True, exist_ok=True)
        (ev / "test_behavior.py").write_text(evals[sid], encoding="utf-8")
    return {"id": tid, "steps": steps}


def main() -> int:
    # 复制 6 个 screen 任务
    if OUT.exists():
        for c in list(OUT.iterdir()):
            if c.is_dir():
                shutil.rmtree(c)
            elif c.name != "make_testpart_tasks.py":
                c.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    screen_eps = json.loads(
        (SCREEN / "v13a_screen_tasks.json").read_text(encoding="utf-8")
    )["episodes"]
    episodes = []
    for ep in screen_eps:
        tid = ep["id"]
        shutil.copytree(SCREEN / tid, OUT / tid, dirs_exist_ok=True)
        episodes.append({"id": tid, "steps": ep["steps"]})
    for ep in make_extract_tasks():
        episodes.append(_cumulative_pack(ep))

    # 判别性
    problems = []
    for ep in episodes:
        tid = ep["id"]
        steps = ep["steps"]
        for i, step in enumerate(steps):
            sid = step["id"]
            ev = OUT / tid / "eval" / sid / "test_behavior.py"
            ref = OUT / tid / "reference" / sid
            if _run_eval(ref, ev) != 0:
                problems.append(f"{tid}/{sid} ref FAIL")
            prev = (
                OUT / tid / "reference" / steps[i - 1]["id"]
                if i > 0
                else OUT / tid / "project"
            )
            if _run_eval(prev, ev) == 0:
                problems.append(f"{tid}/{sid} prev PASS want FAIL")

    payload = {
        "schema": "v13a-testpart-tasks-v1",
        "episodes": episodes,
        "discrimination_problems": problems,
    }
    (OUT / "v13a_testpart_tasks.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"testpart tasks={len(episodes)} problems={len(problems)}")
    for p in problems:
        print(" PROBLEM", p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
