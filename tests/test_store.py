"""静态存储测试：必备字段往返、依赖边索引、检索过滤。"""

from __future__ import annotations

from vam_coder.models import MemoryEntry, Validity
from vam_coder.store import StaticStore


def _entry(**over) -> MemoryEntry:
    base = dict(
        symbol_id="demo:core.py::f",
        repo_id="demo",
        file_path="core.py",
        qualified_name="f",
        kind="function",
        content_hash="a" * 64,
        source_hash="a" * 64,
        version=1,
        deps=["demo:core.py::g"],
        summary="f: 3 lines",
        validity=Validity.VALID.value,
        kv_ptr="sim://kv/py-model/aaaa",
        provenance={"task_id": "p0", "outcome": "indexed"},
        size_bytes=64,
        start_line=1,
        end_line=3,
        last_seen_repo_version=1,
        updated_at="2026-10-16T00:00:00+00:00",
    )
    base.update(over)
    return MemoryEntry(**base)


def test_roundtrip_preserves_required_fields(store: StaticStore):
    store.insert_symbol(_entry())
    store.insert_symbol(_entry(
        symbol_id="demo:core.py::g", qualified_name="g",
        deps=[], content_hash="b" * 64, source_hash="b" * 64,
    ))
    store.commit()

    got = store.get("demo:core.py::f")
    assert got is not None
    # 必备字段（用户要求）
    assert got.symbol_id == "demo:core.py::f"
    assert got.content_hash == "a" * 64
    assert got.version == 1
    assert got.deps == ["demo:core.py::g"]
    assert got.summary == "f: 3 lines"
    assert got.validity == Validity.VALID.value
    # 其余元数据
    assert got.kv_ptr == "sim://kv/py-model/aaaa"
    assert got.provenance == {"task_id": "p0", "outcome": "indexed"}

    # 依赖边索引与 JSON 字段一致
    assert store.direct_deps("demo:core.py::f") == ["demo:core.py::g"]
    assert store.direct_dependents("demo:core.py::g") == ["demo:core.py::f"]


def test_repo_version_monotonic(store: StaticStore):
    assert store.get_repo_version("demo") == 0
    assert store.bump_repo_version("demo") == 1
    assert store.bump_repo_version("demo") == 2
    assert store.get_repo_version("demo") == 2
    # 不同仓库互不影响
    assert store.get_repo_version("other") == 0


def test_reopen_persists(store: StaticStore, config):
    store.insert_symbol(_entry())
    store.commit()
    path = config.db_path
    store.close()

    reopened = StaticStore(path)
    try:
        assert reopened.get("demo:core.py::f").validity == Validity.VALID.value
    finally:
        reopened.close()
