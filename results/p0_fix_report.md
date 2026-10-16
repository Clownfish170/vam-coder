# P0 修复验收报告 —— VAM-Coder（Version-Aware Memory Routing for Code Agents）

- 日期：2026-10-16
- 范围：P0 工程正确性修复（任务 A–G）。不训练模型、不接真实 KV Cache、
  不产出/不修改任何性能结果、不改变研究目标。
- 修复前基线：git `37bf61c`（23 tests passed，场景 6/6，退出码均 0）
- 修复后：**63 tests passed（exit 0）**；场景脚本 **ALL PASSED: True（exit 0）**
- 逐文件变更：`PATCH_NOTES.md`；能力边界：`README.md` §5；已知限制：README §6

---

## 1. 逐任务验收

### 任务 A：解析不完整时禁止错误 tombstone —— **通过**
- 实现：`parser.py` 逐文件状态（parsed/partial/read_error/unsupported_language）
  + 仓库根校验抛错；`invalidation.py::_absence_fate` 仅在 parsed 或文件真实
  消失时墓碑，其余 → valid 收紧 unverified（`unconfirmed_symbol` 事件），
  不产生传播种子；`verify` 同规则（读失败/部分解析 → `verify_inconclusive`）。
- 证据：`tests/test_parse_guard.py` 9 项全过（语法错误、读失败、根不存在、
  根非目录、真实删除仍墓碑、语言配置失效、verify 读失败、verify 部分解析、
  verify 根缺失）；9 项在旧实现上全部失败（复现）。
- 幂等：同一坏文件重复同步不产生第二次状态变化（有断言）。

### 任务 B：verify 依赖语义 —— **通过**
- 实现：恢复 = 必要条件（自身重哈希 == content_hash）**且** 充分条件的另一半
  （依赖门控：依赖存在、validity=valid、dep_edges 一致、解析依赖集一致、
  `dep_snapshot` 版本+内容匹配）。不通过 → `verify_blocked`
  （日志含 `content_match` / `deps_ok` / `dep_reasons` 两判断分离）并刷新快照。
  BFS + visited 集 + 512 节点上限 + 跳过自身 → 循环依赖终止（有测试）。
- 未采用“全仓库 unverified”规避。
- 证据：`tests/test_verify_dependencies.py` 8 项全过，覆盖依赖已失效/
  已恢复/被删除/行缺失/边缺失/快照版本失配/循环依赖/日志字段；
  旧实现 8 项全败。`test_invalidation.py::test_dependency_change_...` 中
  旧的“依赖 stale 仍恢复 valid”断言已按正确语义**加强**（PATCH_NOTES §1）。

### 任务 C：跨文件同名符号依赖误连 —— **通过**
- 实现：解析只经 `(file_path, qualified_name)`；优先级 同文件 → import/alias
  绑定（含相对导入）→ 模块限定调用 → 全局唯一裸名（仅 function/class）；
  本地定义与 import 冲突、跨文件同名 → `unresolved_calls`，零猜测边。
  支持边界仍为 Python-only（`skipped_files` 机制与测试不变）。
- 证据：`tests/test_call_resolution.py` 7 项全过；其中“两文件同名+第三方
  调用 / alias / 模块限定 / def+import 冲突”4 项在旧实现失败（复现旧误连或
  旧无法解析）。

### 任务 D：sync 事务一致性 —— **通过**
- 实现：`store.transaction()`（BEGIN IMMEDIATE/COMMIT/ROLLBACK，深度计数，
  内层 `commit()` no-op）；sync 的 B–E 阶段与 verify 全程各为**单一事务**；
  符号文本预读前置，失败在写库前中止。
- 日志策略（如实声明）：JSONL append-only 无法随事务回滚 → 事务内事件仅入
  缓冲、提交后落盘；回滚丢弃缓冲并追加 `sync_aborted`/`verify_aborted`
  （含 `not atomic with the database` 说明）。**不声称日志与数据库原子一致**；
  可审计性质为“回滚不产生半截事件、失败必有显式中止记录”（有断言）。
- 证据：`tests/test_transactions.py` 4 项（异常注入后版本/符号/依赖边全量
  快照与失败前一致、内层 commit 不逃逸、verify 回滚、失败后可恢复）；
  其中 3 项在旧实现失败（复现半截状态问题）。

### 任务 E：请求与决策追踪 —— **通过**
- 实现：`request_id` = 规范化任务内容哈希（NFKC+空白折叠）+ 预算 + 配置摘要
  + 记忆状态；日志记录 episode_id、step_id、request_id、task_content_hash
  与长度、state_digest、config_digest、repo_versions、memory_snapshot、
  逐决策 action/validity/est_tokens/reasons。任务原文**不落日志**（默认哈希）。
- 证据：`tests/test_request_tracking.py` 5 项（同输入可复现、不同任务区分、
  不同状态区分、字段完整+脱敏断言、pipeline 透传）；旧实现 5 项全败。

### 任务 F：类/方法索引与重复失效 —— **通过（行为钉住 + 文档化，零代码改动）**
- 结论：现有语义 = 类哈希含整个类体（含方法）、方法独立哈希；方法变化 →
  类与方法各自 stale（保守，非错误恢复）；闭包 visited 集去重（断言无重复）；
  方法删除 → 方法墓碑、类仅 stale；类 verify 要求整类体匹配。
- 最小修复 = 不重设计符号体系，用测试钉住行为并写入 README §4.6 与
  本报告；避免了未经测试的重设计（符合任务要求）。
- 证据：`tests/test_symbol_granularity.py` 4 项（修复前后均过——预期如此，
  属行为说明书）。

### 任务 G：EXPAND 语义与能力标注 —— **通过**
- 实现：`CAPABILITY_STATUS` 三态标注（symbol_index 等 implemented；
  kv_cache_reuse/summary_generation/token_estimation simulated；
  expand_source_read_and_assembly/model_inference/model_summary_generation
  not_implemented），随每次 route 决策日志落盘；所有 EXPAND reasons 显式
  “routing decision only … not implemented”；`pipeline.py` 文档同步声明
  不执行读取/装配/推理。
- 证据：`tests/test_capabilities.py` 3 项；旧实现 import error（不复现即缺失）。

---

## 2. 测试与场景：命令、真实输出、退出码

| 命令 | 结果 | 退出码 | 输出存档 |
|---|---|---|---|
| `python -m pytest tests/ -v --tb=short`（修复前） | 23 passed | 0 | `results/p0_fix_baseline_pytest.txt` |
| `python scripts/run_p0_scenario.py`（修复前） | 6/6 PASS | 0 | `results/p0_fix_baseline_scenario.txt` |
| `python -m pytest tests/ -v --tb=short`（修复后） | **63 passed** | **0** | `results/p0_fix_pytest_final.txt` |
| `python scripts/run_p0_scenario.py`（修复后） | **6/6 PASS, ALL PASSED: True** | **0** | `results/p0_fix_scenario_final.txt`、`results/p0_scenario_report.json` |
| 新测试 × 旧实现（复现检查） | 29 failed, 1 error, 8 passed | 1 | `results/p0_fix_repro_on_old.txt` |
| 退出码汇总 | — | 0 / 0 | `results/p0_fix_exit_codes.txt` |

- 新增测试 40 项（A9+B8+C7+D4+E5+F4+G3），无删除、无 skip、无放宽的原测试
  （唯一修改的既有断言为按任务 B 加强，见 PATCH_NOTES §1）。
- 未删除/覆盖原始实验结果：修复前输出与旧报告均在基线 commit 与
  `results/p0_fix_baseline_*.txt`；本轮新结果全部使用新文件名。

---

## 3. 仍未解决的问题（如实列出）

1. **调用关系漏检（Python 近似解析）**：无完整 import 时序/遮蔽分析、
   wildcard 不消解、未知对象跨方法调用不解析 → 依赖边可能少建，传播覆盖
   随之缩小（宁漏勿错的反面代价）。P1 应对传播覆盖率抽样量化。
2. **依赖闭包本身是深度上限截断**（closure_depth=2）：d>2 的依赖变化不传播；
   verify 的 BFS 只能补救“显式 verify 的那一个符号”。
3. **部分解析**：语法错误文件在恢复完整解析前，无法区分真删除与解析残缺，
   tombstone 必须等待；其间符号停在 unverified。
4. **循环依赖**：终止性有保证（visited 集）；活性无保证——环内全部
   unverified 时需先由 sync 恢复一环，再逐步 verify 解锁。
5. **事务与 JSONL 非原子**：已按“缓冲+中止事件”策略做到无半截记录与失败
   必有审计，但两者不是一个原子单元（明确不作原子宣称）。
6. **快照门控最多阻一次**：`dep_snapshot` 失配 → 当次拒绝并刷新，下一次
   verify（依赖未再变化）即通过——这是保守的“再确认一次”，不是永久阻断；
   快照只覆盖直接依赖。
7. 无真实 KV、无 LLM 推理、无动态层、无性能数据（能力表已标注，P1/P2）。

## 4. 进入 P1 前必须满足的条件（准入清单）

1. 本文 §1 的 A–G 七项全部“通过”且对应回归测试存在（当前满足）。
2. 全量测试 63 passed + 场景 6/6，退出码 0，且可按 README §1 命令复现（当前满足）。
3. `README.md` §5 能力三态表与日志 `capabilities` 一致，任何输出中不得出现
   “已实现 KV 复用/模型推理/真实 token 测量”的表述（当前满足，有测试锁定）。
4. `PATCH_NOTES.md` 中“既有测试仅一处加强”的事实说明被复核接受。
5. §3 的 7 条未解决项被逐条确认为“可接受的已知限制”或列入 P1 待办
   （至少：漏检覆盖率量化、事务-日志策略在多步 episode 回放下的审计方式）。
6. P1 基线实验开始前冻结本报告对应的 commit，任何后续行为变化需重新跑
   63 项 + 场景并更新本报告。
