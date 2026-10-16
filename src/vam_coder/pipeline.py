"""流程编排：打开存储 → sync（失效管理）→ route（表示路由）。"""

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
    return make_manager(store, config, logger).sync(repo_root, repo_id)


def route_repo(
    store: StaticStore,
    repo_id: str,
    config: AppConfig,
    *,
    budget_tokens: int | None = None,
    include_tombstoned: bool = True,
    request_meta: dict | None = None,
    logger: JsonlLogger | None = None,
) -> RouteResult:
    entries = list(
        store.list_symbols(repo_id, include_tombstoned=include_tombstoned).values()
    )
    router = RuleRouter(config, logger or JsonlLogger(None))
    return router.route(
        RouteRequest(
            entries=entries,
            budget_tokens=budget_tokens,
            request_meta=request_meta or {},
        )
    )
