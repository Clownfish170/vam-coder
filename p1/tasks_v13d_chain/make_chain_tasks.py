#!/usr/bin/env python
"""V13D 预览链式任务：每仓 6 个独立 episode（同初始 project → 跨集 sha 可命中）。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

P1 = Path(__file__).resolve().parents[1]
OUT = P1 / "tasks_v13d_chain"


def write_tree(base: Path, files: dict[str, str]) -> None:
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
            encoding="utf-8",
            errors="replace",
        )
        return r.returncode


PROJ_A = {
    "engine.py": (
        "from price_table import RATE\n\n\n"
        "def quote(x):\n    return x\n\n\n"
        "def discount(x):\n    return x\n"
    ),
    "price_table.py": (
        "RATE = 10\n"
        "TAX = 1\n"
        "NAME = 'chainA'\n\n\n"
        "def rate():\n    return RATE\n\n\n"
        "def tax():\n    return TAX\n"
    ),
    "noise.py": "def noise():\n    return 0\n",
}

# 每 episode 一步，指令递进；初始 project 恒为 PROJ_A
STEPS_A = [
    ("请参考 price_table.py 中的 RATE。修改 engine.py 中的 quote(x)：返回 x * RATE。不要修改 price_table.py。",
     {"engine.py": "from price_table import RATE\n\n\ndef quote(x):\n    return x * RATE\n\n\ndef discount(x):\n    return x\n"},
     "def test():\n    from engine import quote\n    assert quote(5) == 50\n"),
    ("请参考 price_table.py 中的 TAX。修改 engine.py 中的 discount(x)：返回 x - TAX。不要修改 price_table.py。",
     {"engine.py": "from price_table import RATE, TAX\n\n\ndef quote(x):\n    return x * RATE\n\n\ndef discount(x):\n    return x - TAX\n"},
     "def test():\n    from engine import discount\n    assert discount(10) == 9\n"),
    ("请在 engine.py 新增 total(x) 返回 quote(x) + discount(x)。不要修改 price_table.py 与 noise.py。",
     {"engine.py": "from price_table import RATE, TAX\n\n\ndef quote(x):\n    return x * RATE\n\n\ndef discount(x):\n    return x - TAX\n\n\ndef total(x):\n    return quote(x) + discount(x)\n"},
     "def test():\n    from engine import total\n    assert total(5) == 54\n"),
    ("请参考 price_table.py 的 RATE。修改 engine.py 中的 quote(x)：x < 0 返回 0，否则 x * RATE。不要修改 price_table.py。",
     {"engine.py": "from price_table import RATE, TAX\n\n\ndef quote(x):\n    if x < 0:\n        return 0\n    return x * RATE\n\n\ndef discount(x):\n    return x - TAX\n\n\ndef total(x):\n    return quote(x) + discount(x)\n"},
     "def test():\n    from engine import quote\n    assert quote(-1) == 0\n    assert quote(5) == 50\n"),
    ("请修改 engine.py 中的 total(x)：返回 quote(x) - discount(x)。不要修改 price_table.py。",
     {"engine.py": "from price_table import RATE, TAX\n\n\ndef quote(x):\n    if x < 0:\n        return 0\n    return x * RATE\n\n\ndef discount(x):\n    return x - TAX\n\n\ndef total(x):\n    return quote(x) - discount(x)\n"},
     "def test():\n    from engine import total\n    assert total(5) == 46\n"),
    ("请修改 engine.py 中的 discount(x)：返回 x - TAX * 2。不要修改 price_table.py。",
     {"engine.py": "from price_table import RATE, TAX\n\n\ndef quote(x):\n    if x < 0:\n        return 0\n    return x * RATE\n\n\ndef discount(x):\n    return x - TAX * 2\n\n\ndef total(x):\n    return quote(x) - discount(x)\n"},
     "def test():\n    from engine import discount\n    assert discount(10) == 8\n"),
]

PROJ_B = {
    "dispatch.py": (
        "from routes import DEFAULT, ALT\n\n\n"
        "def route(key):\n    return DEFAULT\n\n\n"
        "def fallback():\n    return ALT\n"
    ),
    "routes.py": (
        "DEFAULT = 'main'\n"
        "ALT = 'backup'\n"
        "COUNT = 2\n\n\n"
        "def default():\n    return DEFAULT\n\n\n"
        "def count():\n    return COUNT\n"
    ),
    "unused.py": "def unused():\n    return None\n",
}

STEPS_B = [
    ("请参考 routes.py 中的 DEFAULT。修改 dispatch.py 中的 route(key)：当 key 是空字符串 '' 时返回 ALT，其他情况返回 DEFAULT。不要修改 routes.py。",
     {"dispatch.py": "from routes import ALT, DEFAULT\n\n\ndef route(key):\n    if key == '':\n        return ALT\n    return DEFAULT\n\n\ndef fallback():\n    return ALT\n"},
     "def test():\n    from dispatch import route\n    assert route('') == 'backup'\n    assert route('k') == 'main'\n    assert route(None) == 'main'\n"),
    ("请参考 routes.py 中的 COUNT。修改 dispatch.py 中的 fallback()：返回 COUNT。不要修改 routes.py。",
     {"dispatch.py": "from routes import ALT, COUNT, DEFAULT\n\n\ndef route(key):\n    if not key:\n        return ALT\n    return DEFAULT\n\n\ndef fallback():\n    return COUNT\n"},
     "def test():\n    from dispatch import fallback\n    assert fallback() == 2\n"),
    ("请在 dispatch.py 新增 size() 返回 COUNT * 2。不要修改 routes.py 与 unused.py。",
     {"dispatch.py": "from routes import ALT, COUNT, DEFAULT\n\n\ndef route(key):\n    if not key:\n        return ALT\n    return DEFAULT\n\n\ndef fallback():\n    return COUNT\n\n\ndef size():\n    return COUNT * 2\n"},
     "def test():\n    from dispatch import size\n    assert size() == 4\n"),
    ("请参考 routes.py 的 DEFAULT。修改 dispatch.py 中的 route(key)：key == 'x' 返回 ALT。不要修改 routes.py。",
     {"dispatch.py": "from routes import ALT, COUNT, DEFAULT\n\n\ndef route(key):\n    if key == 'x':\n        return ALT\n    if not key:\n        return ALT\n    return DEFAULT\n\n\ndef fallback():\n    return COUNT\n\n\ndef size():\n    return COUNT * 2\n"},
     "def test():\n    from dispatch import route\n    assert route('x') == 'backup'\n    assert route('k') == 'main'\n"),
    ("请修改 dispatch.py 中的 size()：返回 COUNT + 1。不要修改 routes.py。",
     {"dispatch.py": "from routes import ALT, COUNT, DEFAULT\n\n\ndef route(key):\n    if key == 'x':\n        return ALT\n    if not key:\n        return ALT\n    return DEFAULT\n\n\ndef fallback():\n    return COUNT\n\n\ndef size():\n    return COUNT + 1\n"},
     "def test():\n    from dispatch import size\n    assert size() == 3\n"),
    ("请修改 dispatch.py 中的 fallback()：返回 ALT + '!'。不要修改 routes.py。",
     {"dispatch.py": "from routes import ALT, COUNT, DEFAULT\n\n\ndef route(key):\n    if key == 'x':\n        return ALT\n    if not key:\n        return ALT\n    return DEFAULT\n\n\ndef fallback():\n    return ALT + '!'\n\n\ndef size():\n    return COUNT + 1\n"},
     "def test():\n    from dispatch import fallback\n    assert fallback() == 'backup!'\n"),
]


def build_chain(prefix: str, project: dict, steps_spec: list) -> list[dict]:
    out = []
    for i, (instr, ref_files, eval_src) in enumerate(steps_spec, 1):
        tid = f"{prefix}_t{i:02d}"
        # 每个 episode 独立任务目录；初始 project 相同
        write_tree(OUT / tid / "project", project)
        # reference = 初始 + 本步修改（单步 episode）
        ref = dict(project)
        ref.update(ref_files)
        write_tree(OUT / tid / "reference" / "step1", ref)
        ev = OUT / tid / "eval" / "step1"
        ev.mkdir(parents=True, exist_ok=True)
        (ev / "test_behavior.py").write_text(eval_src, encoding="utf-8")
        out.append(
            {
                "id": tid,
                "steps": [{"id": "step1", "instruction": instr, "eval": "eval/step1"}],
                "chain": prefix,
                "order": i,
            }
        )
    return out


def materialize() -> int:
    if OUT.exists():
        for c in list(OUT.iterdir()):
            if c.name == "make_chain_tasks.py":
                continue
            if c.is_dir():
                shutil.rmtree(c)
            else:
                c.unlink()
    OUT.mkdir(parents=True, exist_ok=True)

    episodes = build_chain("chainA", PROJ_A, STEPS_A) + build_chain("chainB", PROJ_B, STEPS_B)
    problems = []
    for ep in episodes:
        tid = ep["id"]
        ref = OUT / tid / "reference" / "step1"
        ev = OUT / tid / "eval" / "step1" / "test_behavior.py"
        if _run_eval(ref, ev) != 0:
            problems.append(f"{tid} ref FAIL")
        if _run_eval(OUT / tid / "project", ev) == 0:
            problems.append(f"{tid} project PASS want FAIL")

    payload = {
        "schema": "v13d-chain-tasks-v1",
        "episodes": episodes,
        "discrimination_problems": problems,
        "note": "each episode 1 step; same initial project within chain; shared SlowStore across chain order",
    }
    (OUT / "v13d_chain_tasks.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"episodes={len(episodes)} problems={len(problems)}")
    for p in problems:
        print(" PROBLEM", p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(materialize())
