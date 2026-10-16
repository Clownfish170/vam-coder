"""流程编排：打开存储 → sync（失效管理）→ route（表示路由）。

动作语义（任务 G）：本模块只编排“失效检测”与“路由决策”两步——
``route_repo`` 返回的是**决策结果**（含 EXPAND 决策），不执行 EXPAND 所
意味着的源码读取、上下文装配、模型推理或 KV 复用（not implemented）。
"""

from __future__ import annotations

from pathlib import Path

from .config import AppConfig
from .invalidation import InvalidationManager, SyncOutcome
from .logging_util import JsonlLogger
from .models import RouteRequest, RouteResult
from .router import RuleRouter
from .store import StaticStore


def open_store(config: AppConfig) -> StaticStore:
    return StaticStore(config.db_path)


def make_manager(
    store: StaticStore, config: AppConfig, logger: JsonlLogger | None = None
) -> InvalidationManager:
    return InvalidationManager(store, config, logger or JsonlLogger(None))


def sync_repo(
    store: StaticStore,
    repo_root: str | Path,
    repo_id: str,
    config: AppConfig,
    logger: JsonlLogger | None = None,
) -> SyncOutcome:
    """同步仓库：仓库根/解析失败会在任何数据库写入前抛错中止。

    只有完整解析（success）的文件允许更新记忆；partial/failed 文件的
    结果不作为权威快照（见 invalidation 规则 3）。
    """
    return make_manager(store, config, logger).sync(repo_root, repo_id)


def route_repo(
    store: StaticStore,
    repo_id: str,
    config: AppConfig,
    *,
    budget_tokens: int | None = None,
    include_tombstoned: bool = True,
    request_meta: dict | None = None,
    episode_id: str | None = None,
    step_id: str | None = None,
    task_content: str | None = None,
    logger: JsonlLogger | None = None,
) -> RouteResult:
    """路由决策（任务 E 追踪字段由调用方可选提供）。

    task_content 只参与 request_id/日志哈希，不会原文写入日志；
    repo_versions 取库中当前仓库版本，随决策日志落盘。
    """
    entries = list(
        store.list_symbols(repo_id, include_tombstoned=include_tombstoned).values()
    )
    repo_versions = {
        rid: store.get_repo_version(rid)
        for rid in sorted({e.repo_id for e in entries})
    }
    router = RuleRouter(config, logger or JsonlLogger(None))
    return router.route(
        RouteRequest(
            entries=entries,
            budget_tokens=budget_tokens,
            request_meta=request_meta or {},
            episode_id=episode_id,
            step_id=step_id,
            task_content=task_content,
            repo_versions=repo_versions,
        )
    )
