"""任务 E 回归测试：request_id 可复现且能区分任务，日志字段完整且脱敏。

- 相同规范化任务内容 + 相同状态 → 相同 request_id（可复现）；
- 不同任务内容（即使预算/配置/记忆状态相同）→ 不同 request_id；
- 日志含 episode_id / step_id / request_id / 输入内容哈希 / 配置摘要 /
  记忆快照 / 仓库版本 / 逐条决策字段；任务原文不落日志。
"""

from __future__ import annotations

from vam_coder.logging_util import JsonlLogger
from vam_coder.models import Action, MemoryEntry, RouteRequest, Validity
from vam_coder.router import RuleRouter

TASK_SECRET = "SECRET_TASK_TEXT: fix the login timeout bug"


def make_entry(
    symbol_id: str,
    validity: str = Validity.VALID.value,
    *,
    version: int = 1,
) -> MemoryEntry:
    return MemoryEntry(
        symbol_id=symbol_id,
        repo_id="demo",
        file_path="core.py",
        qualified_name=symbol_id.split("::")[-1],
        kind="function",
        content_hash="h" * 64,
        source_hash="h" * 64,
        version=version,
        deps=[],
        summary="short summary",
        validity=validity,
        kv_ptr="sim://kv/py-model/0123456789abcdef",
        provenance={"task_id": "t", "outcome": "indexed"},
        size_bytes=400,
        start_line=1,
        end_line=10,
        last_seen_repo_version=3,
        updated_at="2026-10-16T00:00:00+00:00",
    )


def _entries() -> list[MemoryEntry]:
    return [
        make_entry("demo:core.py::a", Validity.VALID.value),
        make_entry("demo:core.py::b", Validity.STALE.value, version=2),
        make_entry("demo:core.py::c", Validity.UNVERIFIED.value),
    ]


# ---------- 1. 相同输入相同状态 → request_id 可复现 ----------
def test_same_task_same_state_reproducible(config, tmp_path):
    log_path = tmp_path / "d.jsonl"
    router = RuleRouter(config, JsonlLogger(log_path))
    r1 = router.route(RouteRequest(entries=_entries(),
                                   task_content="Fix the bug"))
    r2 = router.route(RouteRequest(entries=_entries(),
                                   task_content="Fix the bug"))
    # 打乱顺序仍一致（结果只由内容决定）
    r3 = router.route(RouteRequest(entries=list(reversed(_entries())),
                                   task_content="Fix the bug"))
    assert r1.request_id == r2.request_id == r3.request_id
    assert r1.actions() == r3.actions()


# ---------- 2. 不同任务内容 → request_id 可区分 ----------
def test_different_task_content_distinguishes_request_id(config):
    router = RuleRouter(config, JsonlLogger(None))
    r1 = router.route(RouteRequest(entries=_entries(),
                                   task_content="Fix the login bug"))
    r2 = router.route(RouteRequest(entries=_entries(),
                                   task_content="Add a logout endpoint"))
    assert r1.request_id != r2.request_id, (
        "request_id 必须包含规范化任务内容哈希，不能只由状态决定"
    )
    assert r1.task_content_hash != r2.task_content_hash
    # 仅有空白/大小写形式差异（NFKC+空白折叠后一致）→ 视为同一任务
    r3 = router.route(RouteRequest(entries=_entries(),
                                   task_content="  Fix   the login bug  "))
    assert r3.request_id == r1.request_id
    # 未提供任务内容 → 空内容哈希，状态相同则可复现
    r4 = router.route(RouteRequest(entries=_entries()))
    r5 = router.route(RouteRequest(entries=_entries()))
    assert r4.request_id == r5.request_id
    assert r4.request_id != r1.request_id


# ---------- 3. 不同记忆状态 → request_id 可区分 ----------
def test_different_state_distinguishes_request_id(config):
    router = RuleRouter(config, JsonlLogger(None))
    base = RouteRequest(entries=_entries(), task_content="same task")
    changed = RouteRequest(
        entries=[make_entry("demo:core.py::a", Validity.STALE.value)],
        task_content="same task",
    )
    assert router.route(base).request_id != router.route(changed).request_id


# ---------- 4. 日志字段完整 + 不写任务原文 ----------
def test_route_log_fields_complete_and_redacted(config, tmp_path):
    log_path = tmp_path / "d.jsonl"
    router = RuleRouter(config, JsonlLogger(log_path))
    result = router.route(
        RouteRequest(
            entries=_entries(),
            task_content=TASK_SECRET,
            episode_id="ep-007",
            step_id="step-3",
            request_meta={"step": "tracking"},
            repo_versions={"demo": 5},
        )
    )
    events = [e for e in JsonlLogger.read_all(log_path)
              if e["event"] == "route"]
    assert len(events) == 1
    ev = events[0]

    # 追踪字段
    assert ev["episode_id"] == "ep-007"
    assert ev["step_id"] == "step-3"
    assert ev["request_id"] == result.request_id
    assert ev["task_content_hash"] == result.task_content_hash
    assert ev["task_content_hash"] != ""
    assert ev["task_content_chars"] == len(TASK_SECRET)
    assert ev["config_digest"] == result.config_digest
    assert ev["repo_versions"] == {"demo": 5}
    # 记忆快照
    assert ev["memory_snapshot"]["demo:core.py::a"] == {
        "validity": Validity.VALID.value, "version": 1,
    }
    # 逐决策字段
    assert len(ev["decisions"]) == 3
    for d in ev["decisions"]:
        assert d["action"] in {a.value for a in Action}
        assert d["validity"]
        assert isinstance(d["est_tokens"], int)
        assert d["reasons"]

    # 脱敏：任务原文绝不落盘
    raw = log_path.read_text(encoding="utf-8")
    assert TASK_SECRET not in raw
    assert "SECRET_TASK_TEXT" not in raw
    # 结果对象本身也不携带原文
    assert not hasattr(result, "task_content")


# ---------- 5. pipeline 层透传（episode/step/task/repo_versions）----------
def test_pipeline_route_repo_passes_tracking_fields(
    store, config, repo_v1, tmp_path
):
    from vam_coder.pipeline import route_repo, sync_repo

    sync_repo(store, repo_v1, "demo", config)
    log_path = tmp_path / "d.jsonl"
    dlog = JsonlLogger(log_path)
    r = route_repo(
        store, "demo", config, logger=dlog,
        episode_id="ep-9", step_id="s-1",
        task_content="refactor the parser",
        request_meta={"case": "E"},
    )
    ev = [e for e in JsonlLogger.read_all(log_path)
          if e["event"] == "route"][-1]
    assert ev["episode_id"] == "ep-9"
    assert ev["step_id"] == "s-1"
    assert ev["repo_versions"] == {"demo": 1}
    assert ev["task_content_hash"] == r.task_content_hash
    assert "refactor the parser" not in log_path.read_text(encoding="utf-8")
