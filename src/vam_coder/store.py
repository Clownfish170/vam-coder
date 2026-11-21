"""静态记忆存储：SQLite 单文件库（symbols / dep_edges / repo_state）。

表结构说明：
- symbols：symbol_id, content_hash(记忆依据), source_hash(最近观察),
  version, deps(JSON), summary, validity, kv_ptr, provenance, span 等
- dep_edges：依赖边（depender → dependee），symbols.deps 的派生索引
- repo_state：仓库级单调版本号
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .models import MemoryEntry

SCHEMA = """
CREATE TABLE IF NOT EXISTS repo_state (
  repo_id TEXT PRIMARY KEY,
  repo_version INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS symbols (
  symbol_id TEXT PRIMARY KEY,
  repo_id TEXT NOT NULL,
  file_path TEXT NOT NULL,
  qualified_name TEXT NOT NULL,
  kind TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  version INTEGER NOT NULL,
  deps TEXT NOT NULL DEFAULT '[]',
  summary TEXT,
  validity TEXT NOT NULL,
  kv_ptr TEXT,
  provenance TEXT,
  size_bytes INTEGER NOT NULL DEFAULT 0,
  start_line INTEGER NOT NULL DEFAULT 0,
  end_line INTEGER NOT NULL DEFAULT 0,
  last_seen_repo_version INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_symbols_repo ON symbols(repo_id);
CREATE TABLE IF NOT EXISTS dep_edges (
  depender TEXT NOT NULL,
  dependee TEXT NOT NULL,
  PRIMARY KEY (depender, dependee)
);
CREATE INDEX IF NOT EXISTS idx_edges_dependee ON dep_edges(dependee);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _row_to_entry(row: sqlite3.Row) -> MemoryEntry:
    return MemoryEntry(
        symbol_id=row["symbol_id"],
        repo_id=row["repo_id"],
        file_path=row["file_path"],
        qualified_name=row["qualified_name"],
        kind=row["kind"],
        content_hash=row["content_hash"],
        source_hash=row["source_hash"],
        version=row["version"],
        deps=json.loads(row["deps"]),
        summary=row["summary"],
        validity=row["validity"],
        kv_ptr=row["kv_ptr"],
        provenance=json.loads(row["provenance"]) if row["provenance"] else None,
        size_bytes=row["size_bytes"],
        start_line=row["start_line"],
        end_line=row["end_line"],
        last_seen_repo_version=row["last_seen_repo_version"],
        updated_at=row["updated_at"],
    )


class StaticStore:
    """SQLite 存储。

    事务模型（P0 修复 D）：
    - isolation_level=None → 自动提交模式，语句默认即时持久化；
    - 多语句原子性由 :meth:`transaction` 显式管理（BEGIN IMMEDIATE /
      COMMIT / ROLLBACK）；
    - 事务所有权归最外层 ``with store.transaction()``：嵌套调用仅参与
      外层事务，:meth:`commit` 在事务内为 no-op，避免嵌套函数意外提交。
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.isolation_level = None  # 显式事务管理（见类文档）
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self._txn_depth = 0

    # -- 生命周期 --
    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "StaticStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- 事务 --
    @contextmanager
    def transaction(self):
        """外层事务：成功 COMMIT，异常 ROLLBACK；嵌套调用并入外层。

        事务所有权归最外层调用方：内层 ``commit()`` 不会提前提交。
        """
        if self._txn_depth == 0:
            self.conn.execute("BEGIN IMMEDIATE")
        self._txn_depth += 1
        try:
            yield self
        except BaseException:
            self._txn_depth -= 1
            if self._txn_depth == 0:
                self.conn.execute("ROLLBACK")
            raise
        else:
            self._txn_depth -= 1
            if self._txn_depth == 0:
                self.conn.execute("COMMIT")

    def commit(self) -> None:
        """显式提交；处于外层事务中时为 no-op（事务所有权在最外层）。"""
        if self._txn_depth > 0:
            return
        if self.conn.in_transaction:  # 自动提交模式下通常为 False
            self.conn.commit()

    # -- repo 版本 --
    def get_repo_version(self, repo_id: str) -> int:
        row = self.conn.execute(
            "SELECT repo_version FROM repo_state WHERE repo_id = ?", (repo_id,)
        ).fetchone()
        if row is None:
            self.conn.execute(
                "INSERT OR IGNORE INTO repo_state(repo_id, repo_version) "
                "VALUES (?, 0)",
                (repo_id,),
            )
            return 0
        return int(row["repo_version"])

    def bump_repo_version(self, repo_id: str) -> int:
        cur = self.get_repo_version(repo_id)
        new = cur + 1
        self.conn.execute(
            "INSERT INTO repo_state(repo_id, repo_version) VALUES (?, ?) "
            "ON CONFLICT(repo_id) DO UPDATE SET repo_version = excluded.repo_version",
            (repo_id, new),
        )
        self.commit()
        return new

    # -- 条目读写 --
    def get(self, symbol_id: str) -> MemoryEntry | None:
        row = self.conn.execute(
            "SELECT * FROM symbols WHERE symbol_id = ?", (symbol_id,)
        ).fetchone()
        return _row_to_entry(row) if row else None

    def list_symbols(
        self, repo_id: str, include_tombstoned: bool = True
    ) -> dict[str, MemoryEntry]:
        sql = "SELECT * FROM symbols WHERE repo_id = ?"
        if not include_tombstoned:
            sql += " AND validity != 'tombstoned'"
        sql += " ORDER BY symbol_id"
        rows = self.conn.execute(sql, (repo_id,)).fetchall()
        return {r["symbol_id"]: _row_to_entry(r) for r in rows}

    def insert_symbol(self, entry: MemoryEntry) -> None:
        # 允许 tombstoned 符号“复活”（undelete / 重命名回滚）：先删旧行
        self.conn.execute(
            "DELETE FROM symbols WHERE symbol_id = ?", (entry.symbol_id,)
        )
        self.conn.execute(
            """INSERT INTO symbols(
                 symbol_id, repo_id, file_path, qualified_name, kind,
                 content_hash, source_hash, version, deps, summary, validity,
                 kv_ptr, provenance, size_bytes, start_line, end_line,
                 last_seen_repo_version, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                entry.symbol_id, entry.repo_id, entry.file_path,
                entry.qualified_name, entry.kind, entry.content_hash,
                entry.source_hash, entry.version,
                json.dumps(sorted(entry.deps)), entry.summary, entry.validity,
                entry.kv_ptr,
                json.dumps(entry.provenance, ensure_ascii=False, sort_keys=True)
                if entry.provenance else None,
                entry.size_bytes, entry.start_line, entry.end_line,
                entry.last_seen_repo_version, entry.updated_at,
            ),
        )
        self._rebind_edges(entry.symbol_id, entry.deps)

    def apply_source_change(
        self,
        symbol_id: str,
        *,
        source_hash: str,
        version: int,
        validity: str,
        size_bytes: int,
        start_line: int,
        end_line: int,
        repo_version: int,
        deps: list[str],
        summary: str,
        kv_ptr: str | None,
    ) -> None:
        """观察到源码变化：更新 source_hash/几何信息，按调用方语义设置 validity。

        content_hash 不在此处更新——它固定为“记忆建立时的依据”，
        validity=stale 即由 content_hash != source_hash 驱动（可恢复）。
        """
        self.conn.execute(
            """UPDATE symbols SET source_hash=?, version=?, validity=?,
                 size_bytes=?, start_line=?, end_line=?,
                 last_seen_repo_version=?, deps=?, summary=?, kv_ptr=?,
                 updated_at=?
               WHERE symbol_id=?""",
            (
                source_hash, version, validity, size_bytes, start_line,
                end_line, repo_version, json.dumps(sorted(deps)), summary,
                kv_ptr, _now(), symbol_id,
            ),
        )
        self._rebind_edges(symbol_id, deps)

    def set_validity(self, symbol_id: str, validity: str) -> None:
        self.conn.execute(
            "UPDATE symbols SET validity=?, updated_at=? WHERE symbol_id=?",
            (validity, _now(), symbol_id),
        )

    def tombstone(self, symbol_id: str, repo_version: int) -> None:
        self.conn.execute(
            """UPDATE symbols SET validity='tombstoned',
                 last_seen_repo_version=?, updated_at=? WHERE symbol_id=?""",
            (repo_version, _now(), symbol_id),
        )

    def set_content_basis(
        self, symbol_id: str, *, content_hash: str, version: int,
        validity: str, summary: str, kv_ptr: str | None, repo_version: int
    ) -> None:
        """重建记忆（EXPAND 重读后）：更新记忆依据并回到 valid。"""
        self.conn.execute(
            """UPDATE symbols SET content_hash=?, version=?, validity=?,
                 summary=?, kv_ptr=?, last_seen_repo_version=?, updated_at=?
               WHERE symbol_id=?""",
            (content_hash, version, validity, summary, kv_ptr, repo_version,
             _now(), symbol_id),
        )

    def set_provenance(self, symbol_id: str, provenance: dict | None) -> None:
        """仅更新 provenance（如依赖快照），不动版本/validity/哈希。"""
        self.conn.execute(
            "UPDATE symbols SET provenance=?, updated_at=? WHERE symbol_id=?",
            (
                json.dumps(provenance, ensure_ascii=False, sort_keys=True)
                if provenance else None,
                _now(), symbol_id,
            ),
        )

    # -- 依赖边 --
    def _rebind_edges(self, symbol_id: str, deps: list[str]) -> None:
        self.conn.execute("DELETE FROM dep_edges WHERE depender=?", (symbol_id,))
        self.conn.executemany(
            "INSERT OR IGNORE INTO dep_edges(depender, dependee) VALUES (?, ?)",
            [(symbol_id, d) for d in sorted(set(deps))],
        )

    def set_deps(self, symbol_id: str, deps: list[str]) -> None:
        """刷新单个符号的依赖列表（JSON 字段 + 边索引同步）。"""
        self.conn.execute(
            "UPDATE symbols SET deps=?, updated_at=? WHERE symbol_id=?",
            (json.dumps(sorted(deps)), _now(), symbol_id),
        )
        self._rebind_edges(symbol_id, deps)

    def direct_dependents(self, symbol_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT depender FROM dep_edges WHERE dependee=? ORDER BY depender",
            (symbol_id,),
        ).fetchall()
        return [r["depender"] for r in rows]

    def direct_deps(self, symbol_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT dependee FROM dep_edges WHERE depender=? ORDER BY dependee",
            (symbol_id,),
        ).fetchall()
        return [r["dependee"] for r in rows]
