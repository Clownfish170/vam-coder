"""失效管理器：源码变更检测、版本校验、依赖闭包失效、tombstone。

规则（对齐报告 §4.5，closure_depth 默认 2）：
1. 解析哈希 == source_hash（上次观察）→ 完全不变，零状态写入（幂等）。
   仅当解析出的 deps 漂移时刷新依赖边（不动版本/validity）。
2. 解析哈希 != source_hash → 观察到变化：source_hash 更新、version+1；
   若新哈希 == content_hash（记忆依据）→ 源码回退，恢复 valid；
   否则 validity=stale（旧记忆失效，禁止 REUSE_KV）。
   注：content_hash 不更新——它是“记忆建立时的依据”，stale 即由
   content_hash != source_hash 驱动，可被回退或 verify 恢复。
3. 【任务 A + 本轮任务 1】符号消失的推断与一切记忆更新仅在文件
   **success（完整解析）** 时成立：
   - 文件状态 success 且符号缺失 → 删除/重命名 → tombstoned；
   - 文件真实从仓库消失（根校验通过后未再遍历到）→ 同上；
   - partial（部分 AST，非权威）/ failed（读取失败）/ unsupported_language
     → 不得推断删除，**也不得用部分结果覆盖既有内容哈希、依赖边或版本**：
     仅当原状态为 valid 时收紧为 unverified 并记录原因（outcome.unconfirmed），
     其余状态原样保留；部分文件中的新符号不注册，只进
     outcome.incomplete_symbols 诊断。解析恢复正常后按既有规则完整同步。
   - 仓库根不存在/不是目录 → parse_repo 抛错，sync 在任何写入前中止。
4. 集合（2∪3）沿依赖边反向传播 ≤closure_depth 层 → dependents 置
   unverified（已是 stale/tombstoned 的保持原状态；已 unverified 幂等跳过）；
   置 unverified 时在 provenance 记录 dep_snapshot（依赖版本+内容快照）。
   解析不可信文件不产生闭包种子（无法确认的变化不向依赖方传播）。
5. unverified 恢复（任务 B）：verify() 分两个判断——
   a) 自身内容与记忆依据一致（重哈希匹配）是必要条件；
   b) 依赖状态足以支持记忆继续有效是充分条件的另一半：依赖缺失、
      validity≠valid、dep_edges 不一致、解析出的依赖集漂移、或依赖
      快照（版本/内容）不匹配 → 不得恢复 valid，保持/收紧为 unverified
      并刷新快照（再次显式 verify 可复检）。依赖检查为带 visited 集的
      广度优先（循环依赖不递归爆栈），单次检查节点数有上限。
   sync() 不自动治愈 unverified（保守：依赖语义可能已变，需显式校验）。

事务与日志（任务 D）：一次 sync/verify 的全部数据库写入在同一个
store.transaction() 中提交或回滚；JSONL 事件在事务内仅入缓冲，
提交成功后才落盘，回滚则丢弃缓冲并单独追加一条 sync_aborted/
verify_aborted（append-only 日志无法回滚，故不声称与数据库原子一致，
以“无半截事件 + 显式中止记录”为可审计策略）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import AppConfig
from .logging_util import JsonlLogger
from .models import MemoryEntry, SymbolDraft, Validity
from .parser import (
    STATUS_SUCCESS,
    ParseResult,
    extract_import_bindings,
    parse_repo,
    parse_source,
    resolve_dependencies,
)
from .store import StaticStore

# 依赖门控单次检查的节点上限（防病态大图；超出即判定“无法确认”）
MAX_DEPENDENCY_CHECK_NODES = 512


@dataclass
class SyncOutcome:
    repo_id: str
    repo_version_before: int
    repo_version_after: int
    inserted: list[str] = field(default_factory=list)
    content_changed: list[str] = field(default_factory=list)
    reverted: list[str] = field(default_factory=list)
    tombstoned: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    unchanged_count: int = 0
    deps_refreshed: list[str] = field(default_factory=list)
    skipped_files: list[dict] = field(default_factory=list)
    parse_warnings: list[dict] = field(default_factory=list)
    # 任务 A：解析不可信导致的保守收紧（不推断删除）
    unconfirmed: list[dict] = field(default_factory=list)
    snapshot_refreshed: list[str] = field(default_factory=list)
    # 本轮任务 1：部分解析文件中观察到的新符号 —— 未注册，仅诊断
    incomplete_symbols: list[dict] = field(default_factory=list)

    @property
    def mutated(self) -> bool:
        return bool(
            self.inserted or self.content_changed or self.reverted
            or self.tombstoned or self.unconfirmed
        )


def dependency_closure(
    seeds: set[str],
    depth: int,
    direct_dependents,
) -> dict[str, int]:
    """反向依赖闭包：返回 {symbol_id: 层深(1..depth)}，不含 seeds 本身。"""
    visited: set[str] = set(seeds)
    frontier = set(seeds)
    result: dict[str, int] = {}
    for d in range(1, depth + 1):
        nxt: set[str] = set()
        for s in sorted(frontier):
            for p in direct_dependents(s):
                if p not in visited:
                    visited.add(p)
                    nxt.add(p)
                    result[p] = d
        if not nxt:
            break
        frontier = nxt
    return result


def summary_stub(source_text: str, qualified_name: str) -> str:
    """P0 摘要：确定性抽取式（docstring 优先），非模型生成 → 模拟功能。"""
    lines = source_text.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            body = stripped.strip("\"'").strip()
            if body:
                return f"{qualified_name}: {body[:80]}"
    non_empty = [ln for ln in lines if ln.strip()]
    first = non_empty[0].strip() if non_empty else ""
    return f"{qualified_name}: {len(non_empty)} lines; {first[:80]}"


def kv_ptr_stub(content_hash_hex: str) -> str:
    """模拟 KV 分片指针（本阶段不落真实张量）→ 模拟功能。"""
    return f"sim://kv/py-model/{content_hash_hex[:16]}"


class InvalidationManager:
    def __init__(
        self,
        store: StaticStore,
        config: AppConfig,
        logger: JsonlLogger | None = None,
    ):
        self.store = store
        self.config = config
        self.logger = logger or JsonlLogger(None)
        # 事务内事件缓冲（任务 D）：非 None 时不落盘
        self._log_buffer: list[tuple[str, dict]] | None = None

    # ---------- 日志 ----------
    def _log(self, event: str, **payload) -> None:
        if self._log_buffer is not None:
            self._log_buffer.append((event, payload))
        else:
            self.logger.emit(event, **payload)

    def _flush_buffer(self) -> None:
        buf = self._log_buffer
        self._log_buffer = None
        if buf:
            for event, payload in buf:
                self.logger.emit(event, **payload)

    def _abandon_buffer(self, event: str, error: BaseException, **extra) -> None:
        """丢弃缓冲的半截事件，单独写一条可审计的中止记录。"""
        self._log_buffer = None
        self.logger.emit(
            event,
            error=f"{type(error).__name__}: {error}",
            note="database transaction rolled back; buffered per-symbol "
                 "events discarded (JSONL is append-only and not atomic "
                 "with the database)",
            **extra,
        )

    # ---------- 主流程 ----------
    def sync(self, repo_root: str | Path, repo_id: str) -> SyncOutcome:
        # 仓库根校验与解析先于任何数据库写入（任务 A：解析失败不产生状态）
        repo_root = Path(repo_root)
        parsed = parse_repo(repo_root, repo_id, self.config)
        return self.sync_parsed(repo_root, repo_id, parsed)

    @staticmethod
    def _absence_fate(
        parsed: ParseResult, file_path: str, supported_suffixes: set[str]
    ) -> tuple[str, str]:
        """已消失符号的判定：('confirmed', ...) 允许 tombstone；('inconclusive', reason) 不允许。

        confirmed 仅两种：文件解析完整（success）而符号缺失；或受支持后缀的
        文件已整体不存在于遍历结果（真实删除/重命名；仓库根已校验）。
        partial（部分 AST 非权威）、failed（读取失败）、unsupported 一律
        不可推断删除。
        """
        status = parsed.file_status.get(file_path)
        if status is not None:
            if status == STATUS_SUCCESS:
                return "confirmed", "symbol absent from fully parsed file"
            return "inconclusive", f"file_{status}"
        # 文件不在遍历结果中：受支持后缀 → 删除/重命名；否则无法确认
        suffix = Path(file_path).suffix.lower()
        if suffix in supported_suffixes:
            return "confirmed", "file removed or renamed"
        return (
            "inconclusive",
            "file not observed as parsed (removed, renamed, or "
            "language no longer supported)",
        )

    @staticmethod
    def _file_of_symbol_id(symbol_id: str) -> str | None:
        """symbol_id = repo_id:file_path::qname → file_path。"""
        try:
            _, rest = symbol_id.split(":", 1)
            file_path, _qname = rest.rsplit("::", 1)
            return file_path
        except ValueError:
            return None

    def _deps_with_unconfirmable_held(
        self, parsed: ParseResult, new_deps: list[str], old_deps: list[str]
    ) -> list[str]:
        """依赖边裁剪保护（任务 1 + P0.3）。

        - 旧依赖目标**已注册**（在库中）且其文件解析不完整 → 无法确认
          目标消失 → 保留该边，不用部分结果清边；
        - 旧依赖目标**未注册**（如指向 partial 文件中从未登记的符号，
          含历史遗留坏边）→ 悬空边，剪除（不作为正式依赖保留）；
        - 目标文件 success（缺失可信）、文件真实删除（受支持后缀且不在
          遍历）→ 允许移除。
        不会“清空全部依赖”：仅逐条按上述规则判定。
        """
        held: list[str] = []
        for dep in old_deps:
            if dep in new_deps:
                continue
            dep_file = self._file_of_symbol_id(dep)
            if dep_file is None:
                if self.store.get(dep) is not None:
                    held.append(dep)
                continue
            status = parsed.file_status.get(dep_file)
            if status is not None:
                # 未注册目标（含历史坏边）→ 剪除；已注册 + 解析不完整 → 保留
                if status != STATUS_SUCCESS and self.store.get(dep) is not None:
                    held.append(dep)
            else:
                suffix = Path(dep_file).suffix.lower()
                if (
                    suffix not in self.config.supported_languages
                    and self.store.get(dep) is not None
                ):
                    held.append(dep)  # 语言不再支持且目标在库 → 无法确认
        return sorted(set(new_deps) | set(held))

    def sync_parsed(
        self, repo_root: Path, repo_id: str, parsed: ParseResult
    ) -> SyncOutcome:
        cfg = self.config
        before = self.store.get_repo_version(repo_id)
        outcome = SyncOutcome(
            repo_id=repo_id,
            repo_version_before=before,
            repo_version_after=before,
            skipped_files=list(parsed.skipped_files),
            parse_warnings=list(parsed.parse_warnings),
        )
        existing = self.store.list_symbols(repo_id, include_tombstoned=True)

        # ---- 阶段 A0：按文件解析状态分层（任务 1：部分 AST 非权威）----
        # 只有 success 文件的草稿允许参与内容/依赖/删除判定；
        # partial/failed 的草稿仅用于诊断与名称消解索引。
        confirmed_drafts: list[SymbolDraft] = []
        incomplete_drafts: list[SymbolDraft] = []
        for draft in parsed.symbols:
            if parsed.file_status.get(draft.file_path) == STATUS_SUCCESS:
                confirmed_drafts.append(draft)
            else:
                incomplete_drafts.append(draft)
        present = {d.symbol_id for d in confirmed_drafts}

        # ---- 阶段 A：分类（不写库，仅完整解析的草稿）----
        inserts: list[tuple[SymbolDraft, int | None]] = []
        changes: list[tuple[SymbolDraft, MemoryEntry]] = []
        reverts: list[tuple[SymbolDraft, MemoryEntry]] = []
        deps_refresh: list[tuple[str, list[str]]] = []
        for draft in sorted(confirmed_drafts, key=lambda d: d.symbol_id):
            cur = existing.get(draft.symbol_id)
            if cur is None:
                inserts.append((draft, None))
            elif cur.validity == Validity.TOMBSTONED.value:
                # 已 tombstone 的符号重新出现 → 复活，版本接续单调
                inserts.append((draft, cur.version))
            elif draft.content_hash == cur.source_hash:
                merged_deps = self._deps_with_unconfirmable_held(
                    parsed, sorted(draft.deps), sorted(cur.deps)
                )
                if merged_deps != sorted(cur.deps):
                    # 延迟到闭包之后刷新：过早清边会切断 tombstone 的传播路径
                    deps_refresh.append((draft.symbol_id, merged_deps))
                outcome.unchanged_count += 1
            elif draft.content_hash == cur.content_hash:
                reverts.append((draft, cur))
            else:
                changes.append((draft, cur))

        # ---- 阶段 A2：部分 AST 中的草稿 —— 不更新、不注册（任务 1）----
        unconfirmed: list[tuple[str, str]] = []
        incomplete_ids: set[str] = set()
        for draft in sorted(incomplete_drafts, key=lambda d: d.symbol_id):
            incomplete_ids.add(draft.symbol_id)
            status = parsed.file_status.get(draft.file_path)
            cur = existing.get(draft.symbol_id)
            if cur is None:
                # 新符号：不注册为记忆，仅诊断（待完整解析后再索引）
                outcome.incomplete_symbols.append(
                    {
                        "symbol_id": draft.symbol_id,
                        "file_path": draft.file_path,
                        "status": status,
                        "reason": "new symbol observed in incompletely "
                                  "parsed file — not registered as memory; "
                                  "await complete parse",
                    }
                )
            elif cur.validity == Validity.VALID.value:
                # 既有符号：保留原依据与依赖，仅保守收紧（不覆盖哈希/依赖）
                unconfirmed.append(
                    (draft.symbol_id, f"file_{status or 'partial'}")
                )
            # 其余状态（stale/unverified/tombstoned）：原样保留

        # 任务 A：缺失符号逐个判定——仅 success 解析完整才允许 tombstone
        tombstones: list[str] = []
        for sid in sorted(existing):
            entry = existing[sid]
            if sid in present:
                continue
            if sid in incomplete_ids:
                continue  # 已在 A2 处理（收紧或保留），不得 tombstone
            if entry.validity == Validity.TOMBSTONED.value:
                continue
            fate, reason = self._absence_fate(
                parsed, entry.file_path, set(cfg.supported_languages)
            )
            if fate == "confirmed":
                tombstones.append(sid)
            elif entry.validity == Validity.VALID.value:
                # 不可确认 → 保留原状态的保守收紧（不推断删除、不传播闭包）
                unconfirmed.append((sid, reason))

        mutated = bool(
            inserts or changes or reverts or tombstones or unconfirmed
        )

        # 预读插入符号文本（摘要 stub）：先于事务，读失败则中止且未写库
        texts: dict[str, str] = {}
        for draft, _prev in inserts:
            try:
                raw = (repo_root / draft.file_path).read_bytes()
            except OSError as exc:
                raise RuntimeError(
                    f"sync aborted before any database write: cannot re-read "
                    f"{draft.file_path} for symbol {draft.symbol_id}: {exc}"
                ) from exc
            texts[draft.symbol_id] = raw[
                draft.start_byte : draft.end_byte
            ].decode("utf-8", errors="replace")

        # ---- 事务（任务 D）：B+C+D+E 单一提交/回滚 ----
        self._log_buffer = []
        try:
            with self.store.transaction():
                after = (
                    self.store.bump_repo_version(repo_id) if mutated else before
                )

                # ---- 阶段 B：统一应用（repo_version = after）----
                for draft, prev_version in inserts:
                    text = texts[draft.symbol_id]
                    version = 1 if prev_version is None else prev_version + 1
                    entry = MemoryEntry(
                        symbol_id=draft.symbol_id,
                        repo_id=repo_id,
                        file_path=draft.file_path,
                        qualified_name=draft.qualified_name,
                        kind=draft.kind,
                        content_hash=draft.content_hash,
                        source_hash=draft.content_hash,
                        version=version,
                        deps=sorted(draft.deps),
                        summary=summary_stub(text, draft.qualified_name)
                        if cfg.simulate_summary else None,
                        validity=Validity.VALID.value,
                        kv_ptr=kv_ptr_stub(draft.content_hash)
                        if cfg.simulate_kv else None,
                        provenance={
                            "task_id": "p0-sync",
                            "repo_version": after,
                            "outcome": "indexed",
                        },
                        size_bytes=draft.size_bytes,
                        start_line=draft.start_line,
                        end_line=draft.end_line,
                        last_seen_repo_version=after,
                        updated_at=_now_iso(),
                    )
                    self.store.insert_symbol(entry)
                    outcome.inserted.append(draft.symbol_id)
                    self._log(
                        "insert", repo_id=repo_id, symbol_id=draft.symbol_id,
                        version=version, content_hash=draft.content_hash,
                        deps=entry.deps, repo_version=after,
                        reason="new symbol indexed" if prev_version is None
                        else "tombstoned symbol reappeared → resurrected as valid",
                    )

                for draft, cur in changes:
                    new_version = cur.version + 1
                    merged_deps = self._deps_with_unconfirmable_held(
                        parsed, sorted(draft.deps), sorted(cur.deps)
                    )
                    # summary/kv_ptr 是“记忆依据(content_hash)”的产物：依据未变则保留；
                    # 只有 source_hash/version/validity/span/size 跟随当前源码更新
                    self.store.apply_source_change(
                        draft.symbol_id,
                        source_hash=draft.content_hash,
                        version=new_version,
                        validity=Validity.STALE.value,
                        size_bytes=draft.size_bytes,
                        start_line=draft.start_line,
                        end_line=draft.end_line,
                        repo_version=after,
                        deps=merged_deps,
                        summary=cur.summary,
                        kv_ptr=cur.kv_ptr,
                    )
                    outcome.content_changed.append(draft.symbol_id)
                    self._log(
                        "content_stale", repo_id=repo_id,
                        symbol_id=draft.symbol_id,
                        reason="observed source_hash differs from memory basis "
                               "content_hash → stale (REUSE_KV forbidden)",
                        content_hash=cur.content_hash,
                        new_source_hash=draft.content_hash,
                        version=new_version, repo_version=after,
                    )

                for draft, cur in reverts:
                    merged_deps = self._deps_with_unconfirmable_held(
                        parsed, sorted(draft.deps), sorted(cur.deps)
                    )
                    self.store.apply_source_change(
                        draft.symbol_id,
                        source_hash=draft.content_hash,
                        version=cur.version + 1,
                        validity=Validity.VALID.value,
                        size_bytes=draft.size_bytes,
                        start_line=draft.start_line,
                        end_line=draft.end_line,
                        repo_version=after,
                        deps=merged_deps,
                        summary=cur.summary,
                        kv_ptr=cur.kv_ptr,
                    )
                    outcome.reverted.append(draft.symbol_id)
                    self._log(
                        "content_reverted", repo_id=repo_id,
                        symbol_id=draft.symbol_id,
                        reason="source reverted to memory basis content_hash → valid",
                        version=cur.version + 1, repo_version=after,
                    )

                for sid in tombstones:
                    self.store.tombstone(sid, after)
                    outcome.tombstoned.append(sid)
                    self._log(
                        "tombstone", repo_id=repo_id, symbol_id=sid,
                        reason="symbol absent from fully parsed/observed file "
                               "(deleted or renamed) → no longer a valid object",
                        repo_version=after,
                    )

                # 阶段 B'：解析不可信 → valid 收紧为 unverified（不推断删除）
                for sid, why in unconfirmed:
                    self.store.set_validity(sid, Validity.UNVERIFIED.value)
                    outcome.unconfirmed.append(
                        {"symbol_id": sid, "reason": why}
                    )
                    self._log(
                        "unconfirmed_symbol", repo_id=repo_id, symbol_id=sid,
                        reason=f"file state inconclusive ({why}): cannot "
                               f"confirm symbol still exists → valid tightened "
                               f"to unverified (no tombstone inferred)",
                        repo_version=after,
                    )

                # ---- 阶段 C：依赖闭包传播 → unverified（带依赖快照）----
                seeds = set(outcome.content_changed) | set(outcome.tombstoned)
                if seeds:
                    closure = dependency_closure(
                        seeds, cfg.closure_depth, self.store.direct_dependents
                    )
                    for sid in sorted(closure):
                        entry = self.store.get(sid)
                        if entry is None:
                            continue
                        if entry.validity in (
                            Validity.STALE.value, Validity.TOMBSTONED.value
                        ):
                            continue  # 更严重状态优先
                        if entry.validity == Validity.UNVERIFIED.value:
                            continue  # 幂等
                        self._set_unverified_with_snapshot(entry)
                        outcome.unverified.append(sid)
                        self._log(
                            "dependent_unverified", repo_id=repo_id,
                            symbol_id=sid,
                            reason=f"dependency changed within closure depth "
                                   f"{closure[sid]} ≤ {cfg.closure_depth} → "
                                   f"unverified",
                            seeds=sorted(seeds), repo_version=after,
                        )

                # ---- 阶段 D：依赖边刷新（闭包之后，避免切断传播路径）----
                for sid, deps in deps_refresh:
                    self.store.set_deps(sid, deps)
                    outcome.deps_refreshed.append(sid)
                    self._log(
                        "deps_refreshed", repo_id=repo_id, symbol_id=sid,
                        deps=deps,
                        reason="resolved dependency set drifted; "
                               "version/validity untouched",
                    )

                # ---- 阶段 E：unverified 符号的依赖快照刷新（任务 B）----
                for entry in self.store.list_symbols(
                    repo_id, include_tombstoned=False
                ).values():
                    if entry.validity != Validity.UNVERIFIED.value:
                        continue
                    if not entry.deps:
                        continue
                    snap = self._build_dep_snapshot(entry)
                    stored = (entry.provenance or {}).get("dep_snapshot") or {}
                    if snap != stored:
                        prov = dict(entry.provenance or {})
                        prov["dep_snapshot"] = snap
                        self.store.set_provenance(entry.symbol_id, prov)
                        outcome.snapshot_refreshed.append(entry.symbol_id)
                        self._log(
                            "dep_snapshot_refreshed", repo_id=repo_id,
                            symbol_id=entry.symbol_id, dep_snapshot=snap,
                            reason="dependency state re-observed at sync; "
                                   "verify gate compares against this snapshot",
                        )
        except BaseException as exc:
            self._abandon_buffer(
                "sync_aborted", exc, repo_id=repo_id,
                repo_version_before=before,
            )
            raise

        self._flush_buffer()
        outcome.repo_version_after = (
            self.store.get_repo_version(repo_id) if mutated else before
        )
        self.logger.emit(
            "sync_completed", repo_id=repo_id,
            repo_version_before=before,
            repo_version_after=outcome.repo_version_after,
            inserted=outcome.inserted, content_changed=outcome.content_changed,
            reverted=outcome.reverted, tombstoned=outcome.tombstoned,
            unverified=outcome.unverified,
            unchanged_count=outcome.unchanged_count,
            deps_refreshed=outcome.deps_refreshed,
            unconfirmed=outcome.unconfirmed,
            incomplete_symbols=outcome.incomplete_symbols,
            skipped_files=outcome.skipped_files,
            parse_warnings=outcome.parse_warnings,
        )
        return outcome

    # ---------- 依赖快照（任务 B） ----------
    def _build_dep_snapshot(self, entry: MemoryEntry) -> dict[str, dict]:
        snap: dict[str, dict] = {}
        for dep_id in entry.deps:
            dep = self.store.get(dep_id)
            if dep is not None:
                snap[dep_id] = {
                    "version": dep.version,
                    "content_hash": dep.content_hash,
                }
        return snap

    def _set_unverified_with_snapshot(self, entry: MemoryEntry) -> None:
        prov = dict(entry.provenance or {})
        prov["dep_snapshot"] = self._build_dep_snapshot(entry)
        self.store.set_provenance(entry.symbol_id, prov)
        self.store.set_validity(entry.symbol_id, Validity.UNVERIFIED.value)

    def _dependency_gate(
        self, entry: MemoryEntry, fresh_deps: list[str]
    ) -> tuple[bool, list[str]]:
        """依赖状态是否足以支持记忆恢复 valid（任务 B）。

        检查：解析出的依赖集漂移、dep_edges 一致性、逐依赖存在性与
        validity、依赖快照（版本+内容）匹配。BFS 带 visited 集，
        跳过符号自身（循环依赖不爆栈）；节点数超上限判为无法确认。
        """
        reasons: list[str] = []
        if sorted(fresh_deps) != sorted(entry.deps):
            reasons.append(
                f"parsed dependency set {sorted(fresh_deps)} != stored deps "
                f"{sorted(entry.deps)} → dependency relation unconfirmed"
            )
        edge_deps = self.store.direct_deps(entry.symbol_id)
        if edge_deps != sorted(set(entry.deps)):
            reasons.append(
                f"dep_edges {edge_deps} inconsistent with stored deps "
                f"{sorted(entry.deps)} → dependency relation unconfirmed"
            )
        snapshot = (entry.provenance or {}).get("dep_snapshot") or {}
        seen: set[str] = set()
        queue = list(entry.deps)
        nodes = 0
        while queue:
            dep_id = queue.pop(0)
            if dep_id in seen or dep_id == entry.symbol_id:
                continue  # 已访问 / 自身（自身已由内容哈希判断）
            seen.add(dep_id)
            nodes += 1
            if nodes > MAX_DEPENDENCY_CHECK_NODES:
                reasons.append(
                    f"dependency graph exceeds check cap "
                    f"{MAX_DEPENDENCY_CHECK_NODES} → relation unconfirmed"
                )
                break
            dep = self.store.get(dep_id)
            if dep is None:
                reasons.append(f"dependency missing from store: {dep_id}")
                continue
            if dep.validity != Validity.VALID.value:
                reasons.append(
                    f"dependency not trustworthy: {dep_id} "
                    f"validity={dep.validity}"
                )
                continue
            snap = snapshot.get(dep_id)
            if snap is not None and (
                snap.get("version") != dep.version
                or snap.get("content_hash") != dep.content_hash
            ):
                reasons.append(
                    f"dependency snapshot mismatch: {dep_id} "
                    f"recorded(v={snap.get('version')}, "
                    f"h={str(snap.get('content_hash'))[:12]}) current"
                    f"(v={dep.version}, h={dep.content_hash[:12]})"
                )
            queue.extend(dep.deps)
        return (not reasons), reasons

    # ---------- verify（任务 A+B+D） ----------
    def verify(self, symbol_id: str, repo_root: str | Path) -> str:
        """显式校验与恢复（两个判断，任务 B）：

        1) 自身内容与记忆依据一致（重哈希匹配）——必要条件；
        2) 依赖状态足以支持恢复（依赖门控）——充分条件的另一半。
        返回值：valid / stale / tombstoned / unverified（依赖门控不通过）。
        文件读取失败、语法错误（符号未观察到）→ 不推断删除，收紧为
        unverified 并记录原因（任务 A）。全部写入单事务提交/回滚。
        """
        repo_root = Path(repo_root)
        if not repo_root.exists():
            raise FileNotFoundError(f"repo root does not exist: {repo_root}")
        if not repo_root.is_dir():
            raise NotADirectoryError(
                f"repo root is not a directory: {repo_root}"
            )
        entry = self.store.get(symbol_id)
        if entry is None:
            raise KeyError(f"unknown symbol_id: {symbol_id}")
        if entry.validity == Validity.TOMBSTONED.value:
            return entry.validity
        language = self.config.supported_languages.get(
            Path(entry.file_path).suffix.lower()
        )
        if language is None:
            # unsupported：不推断任何状态变化，直接报错（任务 A）
            raise RuntimeError(f"unsupported language: {entry.file_path}")

        self._log_buffer = []
        try:
            with self.store.transaction():
                result = self._verify_locked(entry, repo_root, language)
        except BaseException as exc:
            self._abandon_buffer(
                "verify_aborted", exc, symbol_id=symbol_id
            )
            raise
        self._flush_buffer()
        return result

    def _verify_locked(
        self, entry: MemoryEntry, repo_root: Path, language: str
    ) -> str:
        symbol_id = entry.symbol_id
        repo_id = entry.repo_id
        path = repo_root / entry.file_path

        def bump() -> int:
            return self.store.bump_repo_version(repo_id)

        # --- 文件真实消失（根已校验）→ 允许 tombstone ---
        if not path.is_file():
            after = bump()
            self.store.tombstone(symbol_id, after)
            self._log(
                "verify_tombstone", symbol_id=symbol_id, repo_version=after,
                reason="file missing during verify (repository root "
                       "validated) → file deleted, tombstoned",
            )
            return Validity.TOMBSTONED.value

        # --- 读取失败 → 无法确认，不推断删除 ---
        try:
            src = path.read_bytes()
        except OSError as exc:
            return self._inconclusive(
                entry, f"read_error: {exc}", bump
            )

        drafts, has_error = parse_source(
            src, entry.file_path, repo_id, language
        )
        match = next((d for d in drafts if d.symbol_id == symbol_id), None)

        # --- 解析不完整 → 部分 AST 非权威：一律不结论（任务 1） ---
        # 即使符号被部分提取到，也不得据此写 stale / tombstone / 恢复 valid。
        if has_error:
            observed = "observed" if match is not None else "not observed"
            return self._inconclusive(
                entry,
                f"tree_sitter_has_error (partial parse is not an "
                f"authoritative snapshot; symbol {observed})",
                bump,
            )

        # --- 解析完整但符号缺失 → 删除/重命名 ---
        if match is None:
            after = bump()
            self.store.tombstone(symbol_id, after)
            self._log(
                "verify_tombstone", symbol_id=symbol_id, repo_version=after,
                reason="symbol not found during verify with complete parse "
                       "→ deleted or renamed, tombstoned",
            )
            return Validity.TOMBSTONED.value

        # --- 判断 1：自身内容与记忆依据一致 ---
        content_match = match.content_hash == entry.content_hash
        if not content_match:
            after = bump()
            self.store.apply_source_change(
                symbol_id,
                source_hash=match.content_hash,
                version=entry.version + 1,
                validity=Validity.STALE.value,
                size_bytes=match.size_bytes,
                start_line=match.start_line,
                end_line=match.end_line,
                repo_version=after,
                deps=entry.deps,
                summary=entry.summary,
                kv_ptr=entry.kv_ptr,
            )
            self._log(
                "verify_stale", symbol_id=symbol_id, repo_version=after,
                content_match=False, deps_ok=None,
                reason="rehash mismatch vs content_hash → stale "
                       "(necessary condition failed)",
            )
            return Validity.STALE.value

        # --- 判断 2：依赖状态足以支持恢复（任务 B） ---
        bindings = {
            entry.file_path: extract_import_bindings(
                src, entry.file_path, language
            )
        }
        index_symbols = list(
            self.store.list_symbols(repo_id, include_tombstoned=True).values()
        )
        index_symbols.append(match)
        resolve_dependencies([match], index_symbols, bindings)
        deps_ok, dep_reasons = self._dependency_gate(entry, match.deps)

        if deps_ok:
            snap = self._build_dep_snapshot(entry)
            stored = (entry.provenance or {}).get("dep_snapshot") or {}
            if entry.validity != Validity.VALID.value or snap != stored:
                after = bump()
                prov = dict(entry.provenance or {})
                prov["dep_snapshot"] = snap
                self.store.set_provenance(symbol_id, prov)
                self.store.set_validity(symbol_id, Validity.VALID.value)
                self._log(
                    "verify_confirmed", symbol_id=symbol_id,
                    repo_version=after, content_match=True, deps_ok=True,
                    deps=sorted(entry.deps),
                    reason="content matches memory basis AND all checked "
                           "dependencies present, valid, snapshot-consistent "
                           "→ restore protocol complete → valid",
                )
            else:
                self._log(
                    "verify_confirmed", symbol_id=symbol_id,
                    content_match=True, deps_ok=True,
                    deps=sorted(entry.deps),
                    reason="content matches memory basis AND dependencies "
                           "trustworthy → valid (already valid)",
                )
            return Validity.VALID.value

        # 内容一致但依赖不足以支持 → 不得恢复 valid
        snap = self._build_dep_snapshot(entry)
        stored = (entry.provenance or {}).get("dep_snapshot") or {}
        needs_write = (
            entry.validity != Validity.UNVERIFIED.value or snap != stored
        )
        after = bump() if needs_write else None
        if needs_write:
            prov = dict(entry.provenance or {})
            prov["dep_snapshot"] = snap
            self.store.set_provenance(symbol_id, prov)
            self.store.set_validity(symbol_id, Validity.UNVERIFIED.value)
        log_kwargs = {} if after is None else {"repo_version": after}
        self._log(
            "verify_blocked", symbol_id=symbol_id,
            content_match=True, deps_ok=False, dep_reasons=dep_reasons,
            reason="content matches memory basis (necessary condition) but "
                   "dependency state does not support reuse (sufficient "
                   "condition failed) → not restored to valid; snapshot "
                   "refreshed for the next explicit verify",
            **log_kwargs,
        )
        return Validity.UNVERIFIED.value

    def _inconclusive(
        self, entry: MemoryEntry, why: str, bump
    ) -> str:
        """读取/解析失败：保留原状态；valid 收紧为 unverified（不推断删除）。"""
        if entry.validity == Validity.VALID.value:
            after = bump()
            self.store.set_validity(
                entry.symbol_id, Validity.UNVERIFIED.value
            )
            self._log(
                "verify_inconclusive", symbol_id=entry.symbol_id,
                repo_version=after, content_match=None, deps_ok=None,
                reason=f"cannot verify ({why}): file read/parse failed → "
                       f"no deletion inferred; valid tightened to unverified",
            )
            return Validity.UNVERIFIED.value
        self._log(
            "verify_inconclusive", symbol_id=entry.symbol_id,
            content_match=None, deps_ok=None,
            reason=f"cannot verify ({why}): file read/parse failed → "
                   f"state kept ({entry.validity})",
        )
        return entry.validity


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
