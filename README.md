# VAM-Coder P0 —— 版本感知记忆管理最小可运行原型

依据《DynaMem 查新与方案总报告》§4（VAM-Coder 方案）与 §6（P0 最小原型）实现。
**本阶段只验证工程正确性**：不训练模型、不接入真实 KV 缓存、不产出论文性能数据。

- 实现日期：2026-10-16（P0 修复轮 1：同日；P0 最终轮：同日；**P0.3：同日**，
  修复前基线见 git `37bf61c`）
- Python：3.12.10（要求 ≥ 3.10）
- 平台验证：Windows（win32）；SQLite 3.49.1
- 修复说明：`PATCH_NOTES.md`（轮 1）、`PATCH_NOTES_P0_FINAL.md`（最终轮）
- 验收报告：`results/p0_fix_report.md`（轮 1）、`results/p0_final_acceptance.md`
  （最终轮 + 冻结清单）、`results/p03_acceptance.md`（P0.3）

---

## 1. 干净环境运行（一条命令）

```bash
cd D:\Demo\DynaMem\vam-coder && python -m pip install -r requirements.txt && python -m pytest tests/ -v --tb=short
```

期望输出结尾：`86 passed`（实测 2026-10-16：86 passed in 3.9s，退出码 0；
输出存档 `results/p03_pytest.txt`，退出码 `results/p03_exit_codes.txt`，
环境 `results/p03_env.txt`。历史存档：23 → 63 → 63（各轮修复前）→ 76（最终轮），
见 `results/p0_fix_baseline_pytest.txt` / `p0_fix_pytest_final.txt` /
`p0_final_pre_fix_pytest.txt` / `p0_final_pytest.txt`）。

附：六项必过检查的场景实验（生成实验日志与结果报告）

```bash
python scripts/run_p0_scenario.py
```

期望输出结尾：`ALL PASSED: True`（退出码 0），并生成
`results/p03_scenario_report.json`（**P0.3 起带版本标识**：场景报告不再
写入/覆盖 Git 基线中的 `results/p0_scenario_report.json`；原始基线版本已
归档至 `results/archive_git_37bf61c/`）、`logs/scenario_decisions.jsonl`、
`logs/scenario_invalidation.jsonl`。

---

## 2. 依赖版本（requirements.txt，均为实测锁定）

| 包 | 版本 | 用途 |
|---|---|---|
| tree-sitter | 0.26.0 | AST 解析框架 |
| tree-sitter-python | 0.25.0 | Python grammar |
| blake3 | 1.0.11 | 内容哈希（报告 §4.4） |
| pytest | 9.1.1 | 测试框架 |

仅使用标准库 `sqlite3`（3.49.1）做静态存储，无其它运行时依赖。

---

## 3. 项目结构

```
vam-coder/
├── README.md                  # 本文件
├── PATCH_NOTES.md             # P0 修复轮逐文件变更说明
├── requirements.txt           # 依赖锁定
├── pytest.ini                 # 测试配置（pythonpath=src）
├── .gitignore、.git/          # 修复前基线快照 commit 37bf61c
├── config/
│   └── default.json           # 运行配置（哈希算法/闭包深度/预算/路径）
├── src/vam_coder/             # 源码（与配置/日志/结果分离）
│   ├── models.py              # MemoryEntry / Validity / Action / RouteRequest 等
│   ├── hashing.py             # blake3（可退化 blake2b）
│   ├── config.py              # AppConfig 加载与路由相关字段摘要
│   ├── parser.py              # tree-sitter 符号提取 + 解析状态 + 模块感知依赖消解
│   ├── store.py               # SQLite 静态存储（显式事务，symbols/dep_edges/repo_state）
│   ├── invalidation.py        # 失效管理器：sync / verify 依赖门控 / 闭包 / tombstone
│   ├── router.py              # 规则路由器（四动作 + 预算降级 + 追踪日志 + 能力标注）
│   ├── logging_util.py        # JSONL 实验日志读写（append-only）
│   └── pipeline.py            # 流程编排（open_store/sync_repo/route_repo）
├── tests/                     # 单元 + 集成 + 回归测试（63 项）
│   ├── test_parse_guard.py        # 任务 A：解析不完整禁止错误 tombstone
│   ├── test_verify_dependencies.py# 任务 B：verify 依赖门控
│   ├── test_call_resolution.py    # 任务 C：跨文件同名消歧
│   ├── test_transactions.py       # 任务 D：事务回滚与日志审计
│   ├── test_request_tracking.py   # 任务 E：request_id/日志追踪
│   ├── test_symbol_granularity.py # 任务 F：类/方法粒度语义
│   ├── test_capabilities.py       # 任务 G：能力边界标注
│   ├── test_partial_parse_authority.py  # 最终轮：部分 AST 非权威
│   └── test_import_scoping.py          # 最终轮：函数内 import 作用域
├── scripts/
│   └── run_p0_scenario.py     # 六项必过检查的场景实验（产出实验日志）
├── config/、logs/、results/、state/   # 配置 / 日志 / 测试结果 / 运行时数据库
└── （测试与场景日志写入各自临时目录或 logs/，不污染源码）
```

目录职责分离：**源码 `src/`+`tests/` · 配置 `config/` · 日志 `logs/` · 测试结果 `results/` · 数据库 `state/`**。

---

## 4. 核心模块说明

### 4.1 符号解析 `parser.py`
- Tree-sitter（tree-sitter-python）提取**模块级函数、类、类方法**；
  `symbol_id = repo_id:相对路径::限定名`（报告 §4.3/§4.4）。
- 内容哈希 = 符号节点源字节的 blake3。
- **解析状态（逐文件）**：`ParseResult.file_status` ∈
  **`success`**（读取成功+语法树完整）/ **`partial`**（读取成功但有语法错误，
  部分 AST **非权威**）/ **`failed`**（读取失败）/ **`unsupported_language`**；
  错误细节保留在 `file_errors` 与 `parse_warnings`。仓库根不存在或不是目录
  → `parse_repo` 直接抛 `FileNotFoundError`/`NotADirectoryError`。
- **partial 文件策略（P0 最终轮）**：
  - 仅 `success` 文件允许以本次结果更新符号内容依据、依赖边、版本与
    删除判定；
  - partial/failed：既有符号保留原 `content_hash`/`source_hash`/`deps`，
    原状态为 valid 时收紧为 `unverified`（`unconfirmed_symbol` 事件，
    允许时不给 REUSE_KV）；**不 tombstone**；
  - partial 文件中的新符号**不注册**为记忆，只进 `outcome.incomplete_symbols`
    诊断（`sync_completed` 日志同步落盘）；
  - 依赖边裁剪保护：完整文件中符号的旧依赖若指向解析不完整的文件，
    无法确认目标消失 → 保留该边，不用部分结果清边；
  - `verify` 遇 `has_error` 一律 `verify_inconclusive`（即使符号被部分提取，
    也不写 stale/tombstone/恢复）；
  - 解析恢复 `success` 后按既有规则完整同步（变化→stale、回退→revert、
    可显式 verify 恢复）。
- **依赖消解与 import 作用域（P0 最终轮）**：只经
  `(file_path, qualified_name)` 索引建边；import 分**模块级**（无函数/类
  祖先，含模块级 if/try 内）与**局部**（函数/类体内，嵌套函数计入外层
  符号）——**局部 import 只对其所在函数生效，不泄漏给同文件其他函数**。
  裸名顺序：本符号局部 import → 模块级 import（与同文件 def 冲突则
  ambiguous）→ 同文件模块级定义 → **抑制规则**（同文件其他符号仅有该名的
  局部 import 证据 → 不可靠，unresolved 并记 `detail`）→ 全局唯一裸名
  （仅 function/class）→ unresolved。属性调用同前轮（self/cls、import 绑定、
  模块限定、类限定、同文件唯一对象方法）。
- **可信依赖目标（P0.3 任务 1）**：解析索引（`_RepoIndex`）只装入
  **success 文件**的符号——partial/failed/unsupported 的部分 AST 符号
  保留在 `result.symbols` 作诊断，但**不得成为正式依赖目标**（全局裸名
  回退与 import/模块限定绑定同样被隔离）；无法消歧 → `unresolved_calls`
  含 `detail`。不完整文件恢复 success 后，下一次同步正常建边；已注册目标
  在其文件 partial 期间依赖边保留；从未注册的悬空边（含历史遗留）在
  下一次同步被剪除，verify 对缺失依赖安全拒绝（门控
  `dependency missing from store`）。同文件多符号的模块限定调用可正常
  解析（模块→文件列表已去重）。
- **import 绑定冲突（P0.3 任务 2）**：同作用域同名出现**不同目标**的
  import → 绑定记为 `kind=conflict`，消解时 `ambiguous_name` +
  detail（不按树遍历顺序任选）；同目标重复 import 不算冲突。不实现
  完整 Python 解释器语义（绑定时序等仍为已声明边界）。
- **语言限制（明确记录）**：当前仅支持 `.py`；`.js/.ts/...` 记入
  `skipped_files`。Python 内部限制：嵌套函数/嵌套类不建符号；**不做完整
  Python 作用域语义**（绑定执行顺序、条件导入可达性、重导出链均未分析）；
  `from m import *` 不参与消解。任何无法消歧的调用记
  `unresolved_calls`（含 `detail`），**不建猜测边**。

### 4.2 静态存储 `store.py`（SQLite，任务 D）
`symbols` 表每行保存（用户要求的必备字段加粗）：
**symbol_id、content_hash、version、deps、summary、validity** + repo_id、file_path、
qualified_name、kind、source_hash、kv_ptr、provenance、size/span、
last_seen_repo_version、updated_at。

- `content_hash`：**记忆建立时的依据**（不被当前源码覆盖，stale 语义由此而来）。
- `source_hash`：最近一次观察到的当前源码哈希（幂等变更检测）。
- `dep_edges`：`depender → dependee` 边索引，与 `deps` JSON 字段同事务维护。
- `repo_state`：仓库级单调版本号（有符号变化才 bump）。
- **事务模型**：`isolation_level=None` + 显式 `store.transaction()`
  （BEGIN IMMEDIATE/COMMIT/ROLLBACK）。一次 sync/verify 的全部写入在
  **同一个事务**提交或回滚；事务所有权归最外层 `with`，内层 `commit()`
  为 no-op（防嵌套函数意外提交）。回滚测试见 `test_transactions.py`。
- tombstone 行**保留**（可审计）但 `validity=tombstoned`，默认检索可过滤。

### 4.3 失效管理器 `invalidation.py`（报告 §4.5）
| 规则 | 行为 |
|---|---|
| 源码未变化 | 解析哈希 == `source_hash` → 零状态写入、版本不 bump（幂等，测试 1） |
| 自身内容变化 | `source_hash` 更新、`version+1`、`validity=stale`（测试 2） |
| 源码回退到记忆依据 | 自动恢复 `valid`（`version` 仍 bump） |
| 删除 / 重命名 | **仅当文件解析完整（success）或文件真实从仓库消失**时旧 symbol_id → `tombstoned`；重出现复活并版本接续（测试 4） |
| 解析不可信（任务 A + 最终轮） | `partial`/`failed`/语言失效 → **不推断删除，也不用部分 AST 更新哈希/依赖/版本**：valid 收紧为 `unverified` 并记 `unconfirmed_symbol`，不 bump 依赖传播；partial 文件新符号不注册（`incomplete_symbols` 诊断）；依赖边指向不完整文件时保留旧边；重复同步幂等 |
| 依赖闭包传播 | stale∪tombstoned 为种子，反向依赖 ≤ `closure_depth` 层 → `unverified` 并记录 `dep_snapshot`（依赖版本+内容快照）；不可信文件**不产生种子** |
| 恢复协议（任务 B） | `verify()` 分两个判断：①自身重哈希 == `content_hash`（必要条件）；②**依赖门控**（依赖存在、validity=valid、dep_edges 与解析依赖集一致、快照匹配）→ 全部通过才恢复 `valid`；内容匹配但依赖不足 → 保持/收紧 `unverified` 并刷新快照（`verify_blocked` 事件，可再次显式 verify）。依赖检查为带 visited 集的 BFS（循环依赖不爆栈，上限 512 节点） |
| 读取/解析失败时的 verify | 文件消失（根已校验）→ tombstone；`has_error`（**含符号被部分提取**）→ `verify_inconclusive`，不推断删除、不写 stale、不恢复 valid；读失败同 |
| 依赖边刷新时机 | 置于闭包传播**之后**，避免重命名时过早清边切断传播路径 |
| sync 不自动治愈 unverified | 保守：依赖语义可能已变，需显式校验；但 sync 会刷新 unverified 符号的 `dep_snapshot` |

### 4.4 规则路由器 `router.py`（报告 §4.6 阶段 A，无训练）
逐条目优先级：
1. `tombstoned` → **DROP**（不是有效对象）
2. `stale` / `unverified` → **EXPAND**（**REUSE_KV 被明令禁止**，理由写入日志）
3. 预算超限且有摘要（仅 valid）→ **COMPRESS**
4. `kv_ptr` 可用且 `simulate_kv=true` → **REUSE_KV**
5. 否则 → **EXPAND**

全局预算降级：超预算时按 keep-score = `validity_rank/(est_tokens+1)` 升序逐级降级
（valid：REUSE_KV/EXPAND→COMPRESS→DROP；非 valid：EXPAND→DROP），直到满足预算。

**动作语义（任务 G）**：路由器只输出**动作决策**。EXPAND = “决定重新读取完整
源码”这一决策，**不执行**文件读取、上下文装配、模型推理或 KV 复用
（决策 reasons 显式写明 “routing decision only … not implemented”）。
每次 `route()` 写入决策日志：`request_id`（含**规范化任务内容哈希**+预算+
配置摘要+记忆状态，可复现且可区分不同任务）、`episode_id`/`step_id`（调用方
提供时）、`task_content_hash`/长度（**不落任务原文**）、`repo_versions`、
`memory_snapshot`、`config_digest`、逐条决策 **action + validity +
est_tokens + reasons**、`simulated` 与 `capabilities` 标注。

### 4.5 日志 `logging_util.py`
JSONL 追加写（append-only）：失效事件（`insert/content_stale/content_reverted/
tombstone/dependent_unverified/unconfirmed_symbol/dep_snapshot_refreshed/
verify_confirmed/verify_blocked/verify_stale/verify_tombstone/verify_inconclusive/
verify_aborted/sync_completed/sync_aborted`）与路由决策（`route`），每条带 `reason`。

**数据库与日志的一致性声明（任务 D）**：SQLite 事务**不能**回滚已追加的
JSONL。策略：sync/verify 事务期间事件仅入内存缓冲，**提交成功后才落盘**；
回滚则丢弃缓冲并单独追加一条 `sync_aborted`/`verify_aborted`（含错误与
“not atomic with the database” 说明）。因此日志中**不会出现回滚了的
半截事件**，且失败必有显式中止记录——但**不声称日志与数据库原子一致**。

### 4.6 符号粒度：类与方法（任务 F，行为由测试钉住）
见 `tests/test_symbol_granularity.py`（可执行语义说明书）：
- **类符号哈希 = 整个类体（含所有方法行）的源字节**；方法另有独立
  symbol_id 与独立哈希（= 方法节点字节）。语义：类条目代表“整类定义”，
  任一方法改动都会使类条目 stale（保守，不产生错误恢复）。
- 方法变化 → 类与方法**各自** stale（双重失效并存）；依赖闭包用
  visited 集去重，同一符号**只处理一次**（有测试断言无重复计入）。
- 类体中删除方法 → 方法 `tombstoned`，类仅 stale（类整体仍存在不墓碑）。
- 类 verify 要求**整类体**哈希匹配才可恢复（部分匹配不恢复，有测试）。
- 已知限制：方法同时计入类哈希范围 → 方法级小改动会使类条目失效，
  可能放大 EXPAND 次数；这是保守性代价，非错误恢复（P1 评估粒度收益）。

---

## 5. 已实现 vs 模拟（诚实边界）

能力标注（与日志 `capabilities` 字段一致，测试 `test_capabilities.py` 锁定）：

| 能力 | 标签 | 说明 |
|---|---|---|
| 符号索引、SQLite 存储、哈希/版本失效、依赖闭包、tombstone | **implemented** | 有单元+集成测试 |
| 规则路由器四动作与预算降级（决策层） | **implemented** | 有测试；决策日志可解释 |
| JSONL 实验日志、场景实验报告、中止审计事件 | **implemented** | `logs/`、`results/` |
| request_id/episode/step 追踪与脱敏 | **implemented** | 任务内容只落哈希 |
| **KV 缓存复用** | **simulated** | `kv_ptr` 形如 `sim://kv/py-model/<hash>`，仅作“可用性标志”；**不分配、不复用任何真实张量** |
| **COMPRESS 摘要** | **simulated** | 确定性抽取式 stub（docstring/首行），**非模型生成** |
| token 估算 | **simulated** | `bytes/4` 粗估，非真实 tokenizer |
| **EXPAND 实际读取/装配源码** | **not implemented** | P0 只输出决策 |
| 模型推理 / 模型摘要生成 | **not implemented** | 无 LLM 参与 |
| `simulate_kv=false` 行为 | implemented | 关闭后 REUSE_KV 不可达，回退 EXPAND（为 P2 真实 KV 留开关） |

---

## 6. 未实现功能与已知缺陷（P0 边界，如实列出）

1. **无真实 KV 分片**（P2）：无 safetensors 落盘、无 vLLM prefix caching、无 prefill/显存实测。
2. **无 LLM 参与**：无摘要生成、无主干推理、无任务成功率/延迟指标（P1/P2）。
3. **无动态层**：路由器只见静态记忆条目，不含“当前指令/最新报错”装配与保护。
4. **无学习式路由器**（阶段 B）与任何训练代码——按要求未实现。
5. **多语言**：仅 Python；嵌套函数不建符号；依赖为名称消解（非完整 import 语义）：
   - **漏检风险（有意保守）**：无法消歧的调用记 unresolved（含 `detail`）、
     不建边 → 依赖边可能少建（漏检），传播覆盖不足；**不会**因猜测建边而
     错传（错边已堵死，见 `test_call_resolution.py`、`test_import_scoping.py`）。
   - import 作用域（最终轮）：区分模块级与函数/类局部，局部不跨函数泄漏；
     但**不分析绑定执行顺序**（def 与 import 谁先执行）、条件导入可达性、
     重导出链；`from m import *` 不参与消解；嵌套函数的局部 import 按外层
     被索引符号近似归属（有测试钉住）；类体内 import 仅归属该类符号本身。
   - P0.3：同作用域同名不同目标的 import → conflict → unresolved（保守，
     不按遍历顺序任选）；partial/failed 文件符号不作依赖目标 → 指向它们的
     未注册悬空边在下一次同步被剪除（历史遗留需跑一次 sync 才清理）。
   - 属性调用中未知对象的方法只允许**同文件**唯一匹配；跨文件 `obj.method()`
     不解析（宁漏勿错）。
6. **部分解析（语法错误文件）只能冻结、无法治愈到成功**：该文件的记忆更新
   （哈希/依赖/版本/删除）全部冻结，既有符号停在 unverified、新符号不注册；
   文件恢复可解析（success）前无法区分“真删除”与“解析残缺”，且指向该
   文件的依赖边被保留（不被部分结果清掉）——恢复 success 后按既有规则
   一次性推进（变化→stale、回退→revert、verify 恢复）。
7. **循环依赖**：verify 依赖检查用 visited 集保证终止（有测试）；但环内若
   所有节点同时 unverified 且彼此依赖，需先让其中一个经 sync 回退/重哈希变
   valid 才能逐个解锁（无死锁于正常 sync 流，但环越大恢复步骤越多）。
8. **依赖门控的快照策略**：`dep_snapshot` 不匹配 → 当次拒绝并刷新快照，
   再次显式 verify 可恢复（最多多一步确认）；sync 会顺带刷新 unverified
   符号的快照，正常“sync→verify”流不额外多步。快照只覆盖直接依赖，
   传递依赖只查存在性与 validity（BFS 上限 512 节点，超出判“无法确认”）。
9. **事务与日志非原子**：JSONL append-only 无法随事务回滚；已用“缓冲落盘 +
   中止事件”消除半截记录，但**两者不构成原子一致**（见 §4.5 声明）。
10. **回退自动恢复 `valid`** 依据是“内容与记忆依据完全一致”；外部语义
    （未入库调用方）变化仍属闭包覆盖范围问题，verify 依赖门控只覆盖**库内**
    依赖。
11. **预算 token 为粗估**，COMPRESS/REUSE_KV 成本模型是规则近似。
12. 未接入 git 集成（diff→符号映射用整文件重解析+哈希比较；仓库本身用
    git 保存修复前基线 `37bf61c`）。
13. **未做**并发/多仓库性能优化；SQLite 单连接、单进程。

---

## 7. 测试与实测结果（2026-10-16）

**轮 1 修复前基线**：23 passed，exit 0（`results/p0_fix_baseline_pytest.txt`）。
**轮 1 修复后**：63 passed，exit 0（`results/p0_fix_pytest_final.txt`）。
**最终轮修复前**：63 passed，exit 0（`results/p0_final_pre_fix_pytest.txt`）。

**最终轮修复后全量**：`python -m pytest tests/ -v --tb=short` →
**76 passed，退出码 0**（`results/p0_final_pytest.txt`、
`results/p0_final_exit_codes.txt`）。场景脚本
`python scripts/run_p0_scenario.py` → **ALL PASSED: True，退出码 0**
（`results/p0_final_scenario.txt`、`results/p0_scenario_report.json`；
跨运行 request_id `4794e11220896843`）。

**最终轮新测试在修复前代码上的复现**（存档
`results/p0_final_repro_on_prev.txt`）：`test_partial_parse_authority`(6) +
`test_import_scoping`(7) = 13 项 → **11 failed，2 passed**：
- 11 项失败逐一对应两个问题（partial 覆盖哈希/依赖/误 tombstone/新符号注册/
  verify 写 stale、局部 import 泄漏到兄弟函数等）；
- 2 项通过的说明：模块级 import/alias（修复前已正确，作防回归保留）、
  局部 import 目标模块不存在（修复前后均不建边，原因表述不同）。

| 轮次 | 修复项 | 回归测试 | 结果 |
|---|---|---|---|
| 轮 1 | A–G（解析守卫/依赖门控/同名消歧/事务/追踪/粒度/能力标注） | 40 项（见 `PATCH_NOTES.md`） | **PASSED** |
| 最终轮 | 部分 AST 非权威（任务 1） | `test_partial_parse_authority` 6 项：部分不覆盖哈希/依赖/版本、缺失误 tombstone、新符号不注册、恢复后权威同步、verify 不结论、状态记录 | **PASSED** |
| 最终轮 | 函数内 import 作用域（任务 2） | `test_import_scoping` 7 项：任务书场景作用域、兄弟函数不消歧、模块级+alias、目标缺失不猜测、局部 alias、局部优先于同文件 def、嵌套归属外层 | **PASSED** |
| P0.3 | 不完整符号不作正式依赖目标 + 绑定冲突 + 记录保护 | `test_p03_dependency_targets` 7 项 + `test_import_scoping` 追加 3 项（模块冲突/局部冲突/同目标重复非冲突） | **PASSED** |
| — | 原有测试（各轮唯一调整：状态值重命名断言，强度不变） | `tests/` 原有用例 | **PASSED** |

### P0.3 实测（2026-10-16）

- 修复前既有测试：76 passed，exit 0 → `results/p03_pre_fix_pytest.txt`
- 新测试 × 修复前代码（复现）：**7 failed，10 passed**，exit 1 →
  `results/p03_repro_pre_fix.txt`（失败项 = partial 目标建边、import 绑定
  指向 partial、多符号模块解析误判、恢复建边、悬空边剪除、模块/局部绑定冲突）
- 修复后全量：**86 passed，exit 0** → `results/p03_pytest.txt`；
  场景 **6/6 PASS，exit 0** → `results/p03_scenario.txt` +
  `results/p03_scenario_report.json`；退出码 `results/p03_exit_codes.txt`；
  环境 `results/p03_env.txt`（Python 3.12.10 / tree-sitter 0.26.0 /
  tree-sitter-python 0.25.0 / blake3 1.0.11 / pytest 9.1.1 / sqlite 3.49.1）
- 实验记录来源与冻结判定：`results/p03_acceptance.md`

六项必过检查场景（`results/p03_scenario_report.json`）：C1–C6 **全部 PASS**
（含 verify 恢复协议演示 helper=valid、run=valid）。

---

## 8. 下一阶段 P1 任务清单（基线复现，对应报告 §6 P1）

> P1 目标：memory-off / symbol+full-read / fixed cache / fixed summary 四基线
> 在同 30–50 任务上的结果表；验收 = 至少一条基线相对 memory-off 有可复现差异。

**P0→P1 准入条件（必须全部满足）**：
- 全量测试 86 passed、场景 6/6 PASS（本 README §1 的命令可复现）；
- A–G、最终轮两问题、P0.3 三任务的回归测试存在，且说明了在修复前代码上的
  复现情况（`PATCH_NOTES.md`、`PATCH_NOTES_P0_FINAL.md`、
  `results/p03_acceptance.md`）；
- 日志 `capabilities` 与 `simulated` 标注随决策落盘，无任何“已实现 KV/推理”
  的表述；
- 实验记录来源清晰（原始基线已从 git 归档，本轮输出为 `p03_*` 新文件，
  见 `results/p03_acceptance.md` 来源表）；
- `results/p0_final_acceptance.md` 冻结清单逐项勾选，其中“仍未解决限制”
  已被逐条确认或接受。

1. **任务流构造**：从 Defects4J / SWE-bench Verified 同仓库分组构造 30–50 条
   按依赖排序的多步 episode（5–12 步），公开构造脚本；仓库族划分防泄漏。
2. **接入真实主干**：llama.cpp/vLLM 推理封装（工作区已有 qwen2.5-coder 1.5B），
   统一温度/窗口/预算；输出 token 与端到端延迟、prefill 时间测量（DistServe 口径）。
3. **动态层最小实现**：当前指令 + 最新报错 + 滑动窗口装配，路由器入口并入
   “动态层保护”约束（绝不静默丢弃当前指令/最新报错）。
4. **memory-off 基线**：无跨步记忆，仅当前动态层。
5. **symbol + full-read 基线**：符号检索 + 永远 EXPAND（等价关掉 REUSE_KV/COMPRESS），
   可复用本阶段 `simulate_kv=false` 开关。
6. **fixed cache 基线**：条目写入后无条件 REUSE_KV（绕过 validity 门控，仅作对照，
   需在日志标注“危险基线”）。
7. **fixed summary 基线**：无条件 COMPRESS（摘要仍需 P2 前的模型生成或明确标注 stub）。
8. **stale-citation rate 度量器**：动作是否引用了 `validity≠valid` 的符号 → 规则标注器
   + 小样本人工校验。
9. **指标脚本**：成功率/pass@1、token、p50/p95 延迟、REUSE_KV 触发率、检索/路由耗时；
   冷/热缓存分表；≥3 seeds；含 memory-off 的配对比较。
10. **H1 构造实验雏形**：有校验 vs 无校验（fixed cache）的错误引用率对比——
    为 P2 的 H1 判定铺路。
11. **扩测试面**：episode 级回放测试、多仓库并发索引、报告 §5.2 对照组接口冻结。
12. **止损线执行**：若全部记忆基线 ≤ memory-off → 按报告 §7 转“记忆无效条件分析”支线。

**明确不做**（按用户约束）：完整 Transformer 改造、学习式路由器（阶段 B）、
大规模训练/轨迹生成、真实 KV 分片落盘（P2 事项，P1 仅在需要时打开探针）。

---

## 9. 命令速查

| 用途 | 命令 |
|---|---|
| 安装依赖 | `python -m pip install -r requirements.txt` |
| 全部测试 | `python -m pytest tests/ -v --tb=short` |
| 单条必过测试 | `python -m pytest tests/test_invalidation.py -v` |
| 场景实验（六项检查+日志） | `python scripts/run_p0_scenario.py` |
| 查看修复前基线 | `git show 37bf61c --stat`（基线快照） |
| 查看修复说明 | `type PATCH_NOTES.md`（轮 1）、`type PATCH_NOTES_P0_FINAL.md`（最终轮） |
| 查看验收报告 | `type results\p0_fix_report.md`、`type results\p0_final_acceptance.md`、`type results\p03_acceptance.md` |
| 基线结果归档（git 导出） | `type results\archive_git_37bf61c\MANIFEST.md` |
| 查看路由决策日志 | `type logs\scenario_decisions.jsonl` |
| 查看失效事件日志 | `type logs\scenario_invalidation.jsonl` |
| 查看实验报告（P0.3 起） | `type results\p03_scenario_report.json` |
