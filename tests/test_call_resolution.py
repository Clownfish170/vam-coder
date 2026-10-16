"""任务 C 回归测试：跨文件同名符号不得误连依赖边。

覆盖：同名函数冲突（不建猜测边）、import alias、模块限定调用、
import 消解歧义、本地定义与 import 冲突、同文件作用域优先。
仅 Python（现有 test_unsupported_language_recorded 覆盖语言边界）。
"""

from __future__ import annotations

from pathlib import Path

from vam_coder.parser import parse_repo

from conftest import sid


def _write(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        (root / rel).write_text(text, encoding="utf-8")
    return root


def _by_qname(result) -> dict:
    return {d.qualified_name: d for d in result.symbols}


# ---------- 1. 两文件同名 helper + 第三方调用 → 不建边 ----------
def test_same_name_functions_are_not_guessed(tmp_path: Path, config):
    root = _write(tmp_path / "repo", {
        "a.py": "def helper(x):\n    return 1\n",
        "b.py": "def helper(x):\n    return 2\n",
        "main.py": "def main():\n    return helper(1)\n",
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    # 修复前：by_qname["helper"] 被任意一个文件覆盖 → main 误连其一
    assert by["main"].deps == [], (
        f"跨文件同名不得建边，实际 deps={by['main'].deps}"
    )
    unresolved = [u for u in result.unresolved_calls
                  if u["symbol_id"] == sid("demo", "main.py", "main")]
    assert unresolved and unresolved[0]["reason"] == "ambiguous_name"
    assert unresolved[0]["call"] == "helper"


# ---------- 2. import alias 消解 ----------
def test_import_alias_resolves_to_correct_target(tmp_path: Path, config):
    root = _write(tmp_path / "repo", {
        "a.py": "def helper(x):\n    return 1\n",
        "b.py": "def helper(x):\n    return 2\n",
        "main.py": (
            "from a import helper as h\n"
            "\n"
            "def main():\n"
            "    return h(1)\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["main"].deps == [sid("demo", "a.py", "helper")], (
        "alias h 必须指向 from 来源 a.helper，而非 b.helper"
    )


# ---------- 3. 模块限定调用 ----------
def test_module_qualified_call_resolves(tmp_path: Path, config):
    root = _write(tmp_path / "repo", {
        "a.py": "def helper(x):\n    return 1\n",
        "b.py": "def helper(x):\n    return 2\n",
        "main.py": (
            "import a\n"
            "import b as bee\n"
            "\n"
            "def main():\n"
            "    return a.helper(1)\n"
            "\n"
            "\n"
            "def main2():\n"
            "    return bee.helper(2)\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["main"].deps == [sid("demo", "a.py", "helper")]
    assert by["main2"].deps == [sid("demo", "b.py", "helper")]


# ---------- 4. 有 import 的裸名调用以 import 为准（消除歧义）----------
def test_import_disambiguates_bare_call(tmp_path: Path, config):
    root = _write(tmp_path / "repo", {
        "a.py": "def helper(x):\n    return 1\n",
        "b.py": "def helper(x):\n    return 2\n",
        "main.py": (
            "from b import helper\n"
            "\n"
            "def main():\n"
            "    return helper(1)\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["main"].deps == [sid("demo", "b.py", "helper")]
    assert not [u for u in result.unresolved_calls
                if u["symbol_id"] == sid("demo", "main.py", "main")]


# ---------- 5. 本地定义与 import 同名冲突 → 无法消歧 ----------
def test_local_definition_shadowing_import_is_unresolved(
    tmp_path: Path, config
):
    root = _write(tmp_path / "repo", {
        "a.py": "def helper(x):\n    return 1\n",
        "main.py": (
            "from a import helper\n"
            "\n"
            "def helper(x):\n"
            "    return 2\n"
            "\n"
            "\n"
            "def use():\n"
            "    return helper(1)\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["use"].deps == [], "绑定顺序未分析前不猜测（旧实现会误选）"
    unresolved = [u for u in result.unresolved_calls
                  if u["symbol_id"] == sid("demo", "main.py", "use")]
    assert unresolved and unresolved[0]["reason"] == "ambiguous_name"


# ---------- 6. 同文件作用域优先（回归既有行为）----------
def test_same_file_scope_still_preferred(tmp_path: Path, config):
    root = _write(tmp_path / "repo", {
        "a.py": "def helper(x):\n    return 1\n",
        "main.py": (
            "def helper(x):\n"
            "    return 2\n"
            "\n"
            "\n"
            "def use():\n"
            "    return helper(1)\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["use"].deps == [sid("demo", "main.py", "helper")]


# ---------- 7. 仓库唯一裸名仍可解析（保护既有跨文件依赖）----------
def test_unique_global_name_still_resolves(tmp_path: Path, config):
    root = _write(tmp_path / "repo", {
        "core.py": "def helper(x):\n    return x\n",
        "main.py": "def main():\n    return helper(1)\n",
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["main"].deps == [sid("demo", "core.py", "helper")]
