# PATCH_NOTES —— VAM-Coder P0 正确性修复轮

- 日期：2026-10-16
- 修复前基线：git commit `37bf61c`（`chore: P0 修复前基线快照（pytest 23 passed, scenario 6/6）`），
  可用 `git show 37bf61c:<path>` 取回任意旧文件；旧代码上跑新测试的输出存档
  `results/p0_fix_repro_on_old.txt`。
- 范围：仅工程正确性（任务 A–G）。不训练模型、不接真实 KV、不改研究目标、
  不声称性能收益。未删除/覆盖用户已有数据、日志与数据库（场景脚本按其原有
  设计重生成自身产物，原始结果已在基线 commit 中存档，新结果均为新文件名）。

---

## 1. 修改文件清单与原因

### `src/vam_coder/parser.py`（任务 A + C）
| 变更 | 原因 |
|---|---|
| `ParseResult` 新增 `file_status` / `file_errors` / `import_bindings` | A：逐文件区分 parsed / partial / read_error / unsupported_language，供 sync 判断“缺失”是否可推断为删除 |
| `parse_repo` 先校验仓库根：不存在 → `FileNotFoundError`，非目录 → `NotADirectoryError` | A：旧实现 `rglob` 对不存在根返回空 → 空解析被当“所有符号被删除”→ 全量 tombstone |
| 读取失败 → `status=read_error` 且不产符号（不再静默进入“缺失”分支） | A |
| 语法错误 → `status=partial`，已提取符号仍保留（字节真实可信） | A：区分“部分成功”与“失败” |
| 新增 `extract_import_bindings`（import/from/相对导入/alias/wildcard 记录） | C：把模块身份引入调用解析 |
| 新增 `_RepoIndex` + `_resolve_call` + 重写 `resolve_dependencies`：只经 `(file_path, qualified_name)` 索引建边；优先级 同文件 → import 绑定 → 模块限定 → 全局唯一裸名（仅 function/class） | C：旧实现 `by_qname[短名]` 不含模块身份、字典覆盖任选一个同名函数 → 跨文件误连。歧义/冲突一律 `unresolved_calls`，不建猜测边 |
| `SKIP_DIRS` 增加 `.backup` | 工程卫生（git 后备份目录不再进入索引） |

### `src/vam_coder/store.py`（任务 D，兼顾 B 的快照写入）
| 变更 | 原因 |
|---|---|
| `isolation_level=None`（自动提交模式）+ `transaction()` 上下文管理器（BEGIN IMMEDIATE / COMMIT / ROLLBACK） | D：让一次 sync/verify 的多语句写入可整体提交或回滚 |
| `_txn_depth` 计数 + `commit()` 在事务内为 no-op | D：事务所有权归最外层；旧实现里嵌套调用随时 `conn.commit()` 会提交外层 |
| `get_repo_version` 改 `INSERT OR IGNORE`、去掉无条件 commit；`bump_repo_version` 只在外层请求时 commit | D：bump 曾立即提交 → 后续异常时“版本已加、符号只写一半” |
| 新增 `set_provenance` | B：verify 门控的 `dep_snapshot` 需要只更新 provenance（不动版本/validity/哈希） |

### `src/vam_coder/invalidation.py`（任务 A + B + D）
| 变更 | 原因 |
|---|---|
| `SyncOutcome` 新增 `unconfirmed`（symbol_id+reason）、`snapshot_refreshed`；`mutated` 计入 unconfirmed | A/B 可观测性；unconfirmed 也是一次真实状态收紧，需要 bump 版本 |
| `_absence_fate`：消失符号仅在 **文件 parsed** 或 **受支持后缀文件真实消失** 时进 tombstones；read_error/partial/语言失效 → valid 收紧为 unverified 并记 `unconfirmed_symbol` 事件 | A 核心修复。旧实现一律按“符号缺失=tombstone” |
| 解析不可信文件**不产生闭包种子** | A：无法确认的变化不得向依赖方传播 |
| sync 的 B–E 阶段全部包进单个 `store.transaction()`；插入用的符号文本在开事务**之前**预读，读失败直接抛错中止（未写库） | D |
| 事务内事件进 `_log_buffer`，提交成功后统一落盘；异常 → 丢弃缓冲 + 追加 `sync_aborted` | D：JSONL 无法回滚 → 可审计策略（回滚不产生半截事件，失败必有中止记录；**不声称与数据库原子一致**） |
| 闭包传播置 unverified 时写 `provenance.dep_snapshot`（依赖 version+content_hash）；sync 阶段 E 对 unverified 符号刷新快照 | B：verify 门控需要“依赖版本/内容快照”对照 |
| `verify()` 重写为两判断协议：①内容哈希匹配（必要）；②依赖门控（存在、validity=valid、dep_edges 一致、解析依赖集一致、快照匹配；BFS+visited，上限 512 节点，跳过自身防循环爆栈）→ 全过才恢复 valid；否则 `verify_blocked`（content_match/deps_ok/dep_reasons 入日志）并刷新快照 | B 核心修复。旧实现哈希匹配即恢复 valid，不管依赖仍 stale/unverified/tombstoned |
| verify：根校验前置（缺失/非目录抛错）；文件消失→tombstone；读失败/部分解析未观察到符号→`verify_inconclusive`（valid 收紧 unverified，不推断删除）；unsupported→抛错不改状态 | A 的 verify 侧 |
| verify 全程单事务 + `verify_aborted` 缓冲策略 | D |
| verify 中确有状态变化时才 bump `repo_state`（旧实现给 `last_seen_repo_version` 传 `after+1` 却从不 bump 仓库版本） | 版本语义一致化 |

### `src/vam_coder/models.py`（任务 E）
| 变更 | 原因 |
|---|---|
| `RouteRequest` 新增 `episode_id` / `step_id` / `task_content` / `repo_versions`（均有默认值，兼容旧调用） | E |
| `RouteResult` 新增 `task_content_hash` / `episode_id` / `step_id` / `repo_versions`，`to_dict` 同步输出 | E |

### `src/vam_coder/router.py`（任务 E + G）
| 变更 | 原因 |
|---|---|
| `request_id` payload 加入 `task_content_hash`（NFKC 规范化 + 空白折叠后 blake3） | E：旧 request_id 只由预算/配置/记忆状态决定，不同任务内容可撞同 id |
| 新增 `_normalize_task` / `_task_content_hash`；任务内容只落哈希与长度，**不落原文** | E 脱敏 |
| 决策日志新增 `episode_id`、`step_id`、`task_content_hash`、`task_content_chars`、`state_digest`、`repo_versions`、`memory_snapshot`、`capabilities` | E/G 字段完整性（逐决策 action/validity/est_tokens/reasons 原本已有） |
| 新增 `CAPABILITY_STATUS`（implemented / simulated / not_implemented 三态）并写入日志 | G |
| 所有 EXPAND 分支 reasons 追加 “EXPAND is a routing decision only … not implemented” | G：明确“决定执行 EXPAND”≠“已读取/装配/推理” |

### `src/vam_coder/pipeline.py`（任务 E + G）
| 变更 | 原因 |
|---|---|
| `route_repo` 新增 `episode_id`/`step_id`/`task_content` 透传；自动附 `repo_versions` | E |
| 模块与 `sync_repo` 文档：route 只编排决策；sync 解析失败在写库前中止 | G + A 语义 |

### `src/vam_coder/logging_util.py`
- **未改动**：append-only `emit` 正是缓冲落盘策略依赖的性质；
  缓冲/flush/abandon 全部在 `InvalidationManager` 内实现（避免动公共接口）。

### `tests/test_invalidation.py`（唯一被修改的既有测试）
- `test_dependency_change_marks_dependents_unverified` 中
  “`verify(helper) == valid`（此时依赖 compute 仍 stale）”的断言
  **编码的正是任务 B 要修的缺陷**。修复后语义：此时 verify 必须拒绝恢复
  （返回 unverified），并补充“依赖回退恢复后再 verify → valid”的后半段断言。
- 这是**加强**而非放宽：新增了拒绝路径与二次恢复的断言；其余 22 个既有
  测试一字未动，未删除、未 skip、未放宽。

### `README.md`
- 记录符号粒度/哈希范围/已知限制（任务 F）、实现 vs 模拟边界与能力三态标签
  （任务 G）、事务与日志一致性声明（任务 D）、新测试与实测结果（63 passed）。

### 未修改
- `scripts/run_p0_scenario.py`：六项检查全部原样通过（含 verify 恢复演示
  helper=valid、run=valid），未改动断言；`config/default.json`、`pytest.ini`、
  `requirements.txt` 不需要变化。

---

## 2. 新增测试清单与运行命令

```bash
# 全量（63 项，退出码 0）
python -m pytest tests/ -v --tb=short
# 场景（六项，退出码 0）
python scripts/run_p0_scenario.py
```

| 文件 | 项数 | 任务 |
|---|---|---|
| `tests/test_parse_guard.py` | 9 | A |
| `tests/test_verify_dependencies.py` | 8 | B |
| `tests/test_call_resolution.py` | 7 | C |
| `tests/test_transactions.py` | 4 | D |
| `tests/test_request_tracking.py` | 5 | E |
| `tests/test_symbol_granularity.py` | 4 | F |
| `tests/test_capabilities.py` | 3 | G |
| 合计新增 | 40 | 修复后总数 63（原 23） |

真实输出存档：
- `results/p0_fix_baseline_pytest.txt`（修复前：23 passed，exit 0）
- `results/p0_fix_baseline_scenario.txt`（修复前：ALL PASSED，exit 0）
- `results/p0_fix_pytest_final.txt`（修复后：63 passed，exit 0）
- `results/p0_fix_repro_on_old.txt`（新测试 vs 旧实现：29 failed / 1 error / 8 passed，exit 1）

## 3. 新测试在旧实现上的复现情况（逐项说明）

旧实现 = 基线 `37bf61c`。复现命令：将 7 个新测试文件放入基线代码的 `tests/`
运行 `python -m pytest <新测试> -q --continue-on-collection-errors`。

- **复现（29 failed + 1 collection error）**：A 全部 9 项、B 全部 8 项、
  C 的 4 项（同名冲突/alias/模块限定/def+import 冲突——旧实现分别表现为
  任选一个同名函数、无法解析 alias、无法解析 `mod.func`、误选同名目标）、
  D 的 3 项（旧实现 bump 先提交、异常留下半截状态；嵌套 commit 提交外层）、
  E 全部 5 项（`task_content` 等新参数与字段不存在 → API 层面即失败，
  其中“不同任务内容区分 request_id”在旧逻辑下必然不成立）、G 因
  `CAPABILITY_STATUS` 缺失而 import error。
- **不复现但有明确原因（8 passed）**：
  1. C 的 `test_import_disambiguates_bare_call` / `test_same_file_scope_still_preferred`
     / `test_unique_global_name_still_resolves`：旧实现对这三种输入恰好给出
     正确（或按文件顺序任选后正好命中预期）的结果——保留为防回归用例；
  2. F 全部 4 项：任务 F 明确要求“先增加测试钉住当前行为，再决定最小修复”；
     经测试确认现有行为（类哈希含全类体、方法独立哈希、闭包去重、方法删除
     不墓碑类）自洽且无错误恢复 → **最小修复 = 不改代码**，语义写入
     README §4.6 与测试文件 docstring；
  3. D 的 `test_reads_stable_and_sync_recovers_after_failed_sync`：注入点
     （bump 抛错）恰好落在旧实现首次写入之前，不构成缺陷复现；保留为
     “失败后无悬挂事务”稳定性断言。

## 4. 仍未解决 / 已知限制（详见 README §6）

1. **Python 调用关系漏检风险**：无完整 import 语义/绑定时序分析、
   wildcard 不参与消解、未知对象跨方法调用不解析 → 依赖边**可能少建**
   （漏检方向，宁漏勿错）；漏检会缩小失效传播覆盖面——P1 需量化。
2. **部分解析**：语法错误文件内“真删除 vs 解析残缺”在文件恢复完整解析前
   无法区分；一律保守不墓碑。
3. **循环依赖**：verify 用 visited 集保证终止（有测试）；环内全 unverified
   时需先经 sync 让一环恢复 valid 才能逐步解锁，无活性保证（仅正常流无死锁）。
4. **事务与 JSONL 非原子**：已通过“缓冲 + 中止事件”消除半截日志，但两者
   不构成原子一致（已如实声明，不作原子性宣称）。
5. **verify 依赖门控只覆盖库内依赖**（BFS ≤512 节点 + 直接依赖快照）；
   闭包外的间接变化仍依赖 closure_depth 覆盖，与旧版相同的范围限制。
6. 无真实 KV、无 LLM、无动态层——全部按能力表标注（simulated /
   not_implemented），见 README §5。
