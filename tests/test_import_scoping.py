"""任务 2 回归测试：函数内部 import 的作用域隔离。

- 局部 import 只对其所在函数的调用生效（含 alias）；
- 不泄漏给同文件其他函数（旧实现全树平铺收集 → 泄漏，本文件多项在旧实现
  上失败即复现）；
- 其他函数中的裸名调用不可靠消解 → unresolved（含 detail 原因），不建猜测边；
- 模块级 import / alias 仍按已支持规则工作；
- 保持 Python-only；嵌套函数按外层符号近似归属（见 parser 文档）。
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


# ---------- 1. 任务书场景：局部 import 作用域 ----------
def test_local_import_scoped_to_its_function(tmp_path: Path, config):
    root = _write(tmp_path / "repo", {
        "module_a.py": "def helper():\n    return 1\n",
        "caller.py": (
            "def function_a():\n"
            "    from module_a import helper\n"
            "    return helper()\n"
            "\n"
            "\n"
            "def function_b():\n"
            "    return helper()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    # function_a：尊重其局部 import
    assert by["function_a"].deps == [sid("demo", "module_a.py", "helper")]
    # function_b：不得因 function_a 的局部 import 而连接；无法可靠消解 → unresolved
    assert by["function_b"].deps == [], (
        f"局部 import 泄漏到了 function_b：{by['function_b'].deps}"
    )
    unresolved = [
        u for u in result.unresolved_calls
        if u["symbol_id"] == sid("demo", "caller.py", "function_b")
    ]
    assert unresolved and unresolved[0]["call"] == "helper"
    assert unresolved[0]["reason"] == "ambiguous_name"
    assert "local import" in unresolved[0].get("detail", "")


# ---------- 2. 局部 import + 跨文件同名：function_b 仍不消歧 ----------
def test_local_import_does_not_disambiguate_sibling(
    tmp_path: Path, config
):
    root = _write(tmp_path / "repo", {
        "module_a.py": "def helper():\n    return 1\n",
        "module_b.py": "def helper():\n    return 2\n",
        "caller.py": (
            "def function_a():\n"
            "    from module_a import helper\n"
            "    return helper()\n"
            "\n"
            "\n"
            "def function_b():\n"
            "    return helper()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["function_a"].deps == [sid("demo", "module_a.py", "helper")]
    assert by["function_b"].deps == []
    assert any(
        u["symbol_id"] == sid("demo", "caller.py", "function_b")
        and u["reason"] == "ambiguous_name"
        for u in result.unresolved_calls
    )


# ---------- 3. 模块级 import / alias 仍工作 ----------
def test_module_level_import_and_alias_still_work(
    tmp_path: Path, config
):
    root = _write(tmp_path / "repo", {
        "module_a.py": "def helper():\n    return 1\n",
        "direct.py": (
            "from module_a import helper\n"
            "\n"
            "def use():\n"
            "    return helper()\n"
        ),
        "aliased.py": (
            "from module_a import helper as h\n"
            "\n"
            "def use():\n"
            "    return h()\n"
            "\n"
            "\n"
            "def use2():\n"
            "    return h()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    # 按 file 分组避免重名干扰
    uses = {
        d.file_path: d for d in result.symbols if d.qualified_name == "use"
    }
    assert uses["direct.py"].deps == [sid("demo", "module_a.py", "helper")]
    assert uses["aliased.py"].deps == [sid("demo", "module_a.py", "helper")]
    use2 = next(
        d for d in result.symbols
        if d.file_path == "aliased.py" and d.qualified_name == "use2"
    )
    assert use2.deps == [sid("demo", "module_a.py", "helper")]


# ---------- 4. 局部 import 目标不存在 → 不猜测 ----------
def test_local_import_of_missing_module_is_unresolved(
    tmp_path: Path, config
):
    root = _write(tmp_path / "repo", {
        "caller.py": (
            "def function_a():\n"
            "    from ghost import helper\n"
            "    return helper()\n"
            "\n"
            "\n"
            "def function_b():\n"
            "    return helper()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["function_a"].deps == [], "目标模块不存在 → 不建边"
    assert by["function_b"].deps == [], "其他函数不得继承该局部 import"
    reasons = {
        u["symbol_id"].rsplit("::", 1)[-1]: u for u in result.unresolved_calls
    }
    assert "function_a" in reasons and "function_b" in reasons


# ---------- 5. 局部 import alias 作用域 ----------
def test_local_import_alias_scoped(tmp_path: Path, config):
    root = _write(tmp_path / "repo", {
        "module_a.py": "def helper():\n    return 1\n",
        "caller.py": (
            "def function_a():\n"
            "    from module_a import helper as h\n"
            "    return h()\n"
            "\n"
            "\n"
            "def function_b():\n"
            "    return h()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["function_a"].deps == [sid("demo", "module_a.py", "helper")]
    # h 只在 function_a 局部可见：function_b 的 h() 不可消解
    assert by["function_b"].deps == []
    assert any(
        u["symbol_id"] == sid("demo", "caller.py", "function_b")
        and u["call"] == "h"
        for u in result.unresolved_calls
    )


# ---------- 6. 模块级同名 def 与局部 import 共存（函数内局部优先）----------
def test_local_import_shadows_same_file_module_def_inside_function(
    tmp_path: Path, config
):
    root = _write(tmp_path / "repo", {
        "module_a.py": "def helper():\n    return 1\n",
        "caller.py": (
            "def helper():\n"
            "    return 0\n"
            "\n"
            "\n"
            "def function_a():\n"
            "    from module_a import helper\n"
            "    return helper()\n"
            "\n"
            "\n"
            "def function_b():\n"
            "    return helper()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    # 函数内局部 import 覆盖模块级同名 def（函数作用域优先，确定性）
    assert by["function_a"].deps == [sid("demo", "module_a.py", "helper")]
    # function_b 无局部 import → 同文件模块级 def（唯一匹配）
    assert by["function_b"].deps == [sid("demo", "caller.py", "helper")]


# ---------- 7. 嵌套函数的局部 import 归属外层符号（近似，文档化）----------
def test_nested_function_local_import_attributed_to_outer(
    tmp_path: Path, config
):
    root = _write(tmp_path / "repo", {
        "module_a.py": "def helper():\n    return 1\n",
        "caller.py": (
            "def outer():\n"
            "    def inner():\n"
            "        from module_a import helper\n"
            "        return helper()\n"
            "    return inner()\n"
            "\n"
            "\n"
            "def sibling():\n"
            "    return helper()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    # 嵌套函数不建符号：其调用与局部 import 均计入外层 outer
    assert by["outer"].deps == [sid("demo", "module_a.py", "helper")]
    # sibling 不受 outer 内部 import 影响 → unresolved
    assert by["sibling"].deps == []


# ---------- 8. 同作用域重复绑定冲突 → unresolved（任务 2）----------
def test_conflicting_module_imports_are_unresolved(
    tmp_path: Path, config
):
    """from a import helper + from b import helper：不得按树遍历顺序任选。"""
    root = _write(tmp_path / "repo", {
        "a.py": "def helper():\n    return 1\n",
        "b.py": "def helper():\n    return 2\n",
        "main.py": (
            "from a import helper\n"
            "from b import helper\n"
            "\n"
            "def use():\n"
            "    return helper()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["use"].deps == [], (
        f"冲突 import 被任选其一解析：{by['use'].deps}"
    )
    unresolved = [
        u for u in result.unresolved_calls
        if u["symbol_id"] == sid("demo", "main.py", "use")
    ]
    assert unresolved and unresolved[0]["reason"] == "ambiguous_name"
    assert "conflict" in unresolved[0].get("detail", "")


def test_conflicting_local_imports_are_unresolved(
    tmp_path: Path, config
):
    """同一函数内重复绑定冲突同样保守 unresolved。"""
    root = _write(tmp_path / "repo", {
        "a.py": "def helper():\n    return 1\n",
        "b.py": "def helper():\n    return 2\n",
        "main.py": (
            "def use():\n"
            "    from a import helper\n"
            "    from b import helper\n"
            "    return helper()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["use"].deps == []
    unresolved = [
        u for u in result.unresolved_calls
        if u["symbol_id"] == sid("demo", "main.py", "use")
    ]
    assert unresolved and unresolved[0]["reason"] == "ambiguous_name"
    assert "conflict" in unresolved[0].get("detail", "")


def test_identical_duplicate_import_not_a_conflict(
    tmp_path: Path, config
):
    """同目标重复 import（含 import a.b 与 import a 同头名）不误判冲突。"""
    root = _write(tmp_path / "repo", {
        "a.py": "def helper():\n    return 1\n",
        "main.py": (
            "from a import helper\n"
            "from a import helper\n"
            "\n"
            "def use():\n"
            "    return helper()\n"
            "\n"
            "\n"
            "def use2():\n"
            "    import a\n"
            "    import a\n"
            "    return a.helper()\n"
        ),
    })
    result = parse_repo(root, "demo", config)
    by = _by_qname(result)
    assert by["use"].deps == [sid("demo", "a.py", "helper")]
    assert by["use2"].deps == [sid("demo", "a.py", "helper")]
