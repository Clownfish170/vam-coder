"""核心数据模型：符号草稿（解析产物）、记忆条目、路由决策。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Validity(str, Enum):
    """记忆条目有效性状态（由 InvalidationManager 维护）。"""

    VALID = "valid"
    STALE = "stale"            # 自身内容哈希变化，旧记忆失效
    UNVERIFIED = "unverified"  # 依赖闭包传播：依赖方变化，待重哈希校验
    TOMBSTONED = "tombstoned"  # 符号被删除或重命名，不再是有效对象


class Action(str, Enum):
    """表示路由器动作空间。"""

    REUSE_KV = "REUSE_KV"
    COMPRESS = "COMPRESS"
    EXPAND = "EXPAND"
    DROP = "DROP"


class SymbolKind(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"


@dataclass
class SymbolDraft:
    """Parser 输出的单个符号（deps 在仓库级两趟解析后回填）。"""

    symbol_id: str
    repo_id: str
    file_path: str          # 相对仓库根的 posix 路径
    qualified_name: str
    kind: str
    content_hash: str       # 该符号源字节的哈希
    size_bytes: int
    start_line: int         # 1-based
    end_line: int
    start_byte: int
    end_byte: int
    deps: list[str] = field(default_factory=list)
    raw_calls: list[str] = field(default_factory=list)


@dataclass
class MemoryEntry:
    """静态层记忆条目（对应 SQLite symbols 表一行）。

    content_hash / version / deps 描述“这条记忆建立时所依据的源码”；
    source_hash 描述“最近一次观察到的当前源码”，用于幂等变更检测。
    """

    symbol_id: str
    repo_id: str
    file_path: str
    qualified_name: str
    kind: str
    content_hash: str
    source_hash: str
    version: int
    deps: list[str]
    summary: str | None
    validity: str
    kv_ptr: str | None
    provenance: dict | None
    size_bytes: int
    start_line: int
    end_line: int
    last_seen_repo_version: int
    updated_at: str


@dataclass
class RouteDecision:
    symbol_id: str
    action: str
    validity: str
    est_tokens: int
    reasons: list[str]

    def to_dict(self) -> dict:
        return {
            "symbol_id": self.symbol_id,
            "action": self.action,
            "validity": self.validity,
            "est_tokens": self.est_tokens,
            "reasons": list(self.reasons),
        }


@dataclass
class RouteRequest:
    entries: list[MemoryEntry]
    budget_tokens: int | None = None
    request_meta: dict = field(default_factory=dict)
    # 可复现的请求标识 + 追踪维度（调用方可选提供）
    episode_id: str | None = None
    step_id: str | None = None
    task_content: str | None = None   # 仅用于哈希，绝不原样写入日志
    repo_versions: dict[str, int] = field(default_factory=dict)


@dataclass
class RouteResult:
    request_id: str
    budget_tokens: int
    total_estimated_tokens: int
    decisions: list[RouteDecision]
    config_digest: str
    # 追踪字段（request_id 含任务内容哈希，不同任务可区分）
    task_content_hash: str = ""
    episode_id: str | None = None
    step_id: str | None = None
    repo_versions: dict[str, int] = field(default_factory=dict)

    def actions(self) -> dict[str, str]:
        return {d.symbol_id: d.action for d in self.decisions}

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "budget_tokens": self.budget_tokens,
            "total_estimated_tokens": self.total_estimated_tokens,
            "config_digest": self.config_digest,
            "task_content_hash": self.task_content_hash,
            "episode_id": self.episode_id,
            "step_id": self.step_id,
            "repo_versions": dict(self.repo_versions),
            "decisions": [d.to_dict() for d in self.decisions],
        }
