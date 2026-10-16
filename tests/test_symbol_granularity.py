"""任务 F：类/方法索引与重复失效——先用测试钉住当前行为。

当前语义（P0 决定保留，README §4.6 有说明）：
- 类符号哈希 = 整个类体（含方法）源字节；方法另有独立符号与独立哈希；
- 方法变化 → 类与方法各自判 stale（双重失效是保守语义，不是错误恢复）；
- 闭包传播用 visited 集去重 → 同一符号不会被重复处理；
- 类体中删除方法 → 方法 tombstoned、类 stale（类整体仍存在，不墓碑）。
本文件即“语义说明书”的可执行版本；若未来重设计符号粒度，先改这些测试。
"""

from __future__ import annotations

from pathlib import Path

from vam_coder.hashing import content_hash
from vam_coder.invalidation import InvalidationManager
from vam_coder.logging_util import JsonlLogger
from vam_coder.models import Validity
from vam_coder.parser import parse_repo

from conftest import sid

V1 = {
    "obj.py": (
        "class Calc:\n"
        "    def run(self, x):\n"
        "        return x + 1\n"
        "\n"
        "\n"
        "def make():\n"
        "    return Calc()\n"
        "\n"
        "\n"
        "def both(x):\n"
        "    c = Calc()\n"
        "    return c.run(x)\n"
    ),
}

# 方法体变化（类体随之变化，方法独立哈希也变化）
V2_METHOD_CHANGED = {
    "obj.py": V1["obj.py"].replace("return x + 1", "return x + 100"),
}

# 删除方法（类仍在）
V2_METHOD_REMOVED = {
    "obj.py": (
        "class Calc:\n"
        "    pass\n"
        "\n"
        "\n"
        "def make():\n"
        "    return Calc()\n"
        "\n"
        "\n"
        "def both(x):\n"
        "    c = Calc()\n"
        "    return c.run(x)\n"
    ),
}


def _write(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        (root / rel).write_text(text, encoding="utf-8")
    return root


def _manager(store, config, tmp_path) -> InvalidationManager:
    return InvalidationManager(store, config, JsonlLogger(tmp_path / "inv.jsonl"))


# ---------- 1. 类哈希覆盖整个类体；方法有独立符号与哈希 ----------
def test_class_hash_covers_body_methods_standalone(tmp_path, config):
    repo = _write(tmp_path / "repo", dict(V1))
    result = parse_repo(repo, "demo", config)
    by_id = {d.symbol_id: d for d in result.symbols}
    cls = by_id[sid("demo", "obj.py", "Calc")]
    method = by_id[sid("demo", "obj.py", "Calc.run")]

    src = (repo / "obj.py").read_bytes()
    # 类哈希 = 整类体（含方法行）的源字节哈希
    assert cls.content_hash == content_hash(
        src[cls.start_byte:cls.end_byte]
    )
    assert cls.start_line <= method.start_line <= cls.end_line
    assert method.end_line <= cls.end_line
    # 方法哈希 = 方法节点字节（范围更小，与类哈希不同）
    assert method.content_hash == content_hash(
        src[method.start_byte:method.end_byte]
    )
    assert method.content_hash != cls.content_hash
    assert cls.kind == "class" and method.kind == "method"


# ---------- 2. 方法变化 → 类与方法都 stale；传播去重 ----------
def test_method_change_invalidates_class_and_method_once(
    store, config, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = _write(tmp_path / "repo", dict(V1))
    mgr.sync(repo, "demo")

    _write(repo, dict(V2_METHOD_CHANGED))
    out = mgr.sync(repo, "demo")

    cls_id = sid("demo", "obj.py", "Calc")
    method_id = sid("demo", "obj.py", "Calc.run")
    # 双重失效：类（整体哈希变）与方法（自身哈希变）各自 stale
    assert cls_id in out.content_changed
    assert method_id in out.content_changed
    assert store.get(cls_id).validity == Validity.STALE.value
    assert store.get(method_id).validity == Validity.STALE.value
    # 依赖方（make 只依赖类、both 依赖类+方法）各处理一次，不重复
    assert out.unverified.count(sid("demo", "obj.py", "make")) == 1
    assert out.unverified.count(sid("demo", "obj.py", "both")) == 1
    assert len(out.unverified) == len(set(out.unverified)), (
        "闭包传播必须去重，不得重复计入"
    )
    assert store.get(sid("demo", "obj.py", "both")).validity == (
        Validity.UNVERIFIED.value
    )


# ---------- 3. 类 verify 不会因部分匹配而误恢复 ----------
def test_class_verify_requires_full_body_match(
    store, config, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = _write(tmp_path / "repo", dict(V1))
    mgr.sync(repo, "demo")
    _write(repo, dict(V2_METHOD_CHANGED))
    mgr.sync(repo, "demo")

    cls_id = sid("demo", "obj.py", "Calc")
    # 类体已变（方法改了）→ 哈希失配 → 保持 stale，绝不恢复 valid
    assert mgr.verify(cls_id, repo) == Validity.STALE.value
    assert store.get(cls_id).validity == Validity.STALE.value
    # 方法同样失配
    assert mgr.verify(sid("demo", "obj.py", "Calc.run"), repo) == (
        Validity.STALE.value
    )
    # 回到原类体 → 类可恢复（类自身无依赖，门控通过）
    _write(repo, dict(V1))
    mgr.sync(repo, "demo")
    assert mgr.verify(cls_id, repo) == Validity.VALID.value


# ---------- 4. 方法删除：方法 tombstone，类 stale 而非 tombstone ----------
def test_method_removal_tombstones_method_not_class(
    store, config, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = _write(tmp_path / "repo", dict(V1))
    mgr.sync(repo, "demo")

    _write(repo, dict(V2_METHOD_REMOVED))
    out = mgr.sync(repo, "demo")

    method_id = sid("demo", "obj.py", "Calc.run")
    cls_id = sid("demo", "obj.py", "Calc")
    assert method_id in out.tombstoned
    assert store.get(method_id).validity == Validity.TOMBSTONED.value
    # 类整体仍在解析结果中 → 只因类体变化而 stale
    assert cls_id not in out.tombstoned
    assert store.get(cls_id).validity == Validity.STALE.value
    # both 依赖方法 → 被 tombstone 种子传播为 unverified
    assert store.get(sid("demo", "obj.py", "both")).validity == (
        Validity.UNVERIFIED.value
    )
