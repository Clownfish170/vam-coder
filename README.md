# VAM-Coder P0 —— 版本感知记忆管理最小可运行原型

依据《DynaMem 查新与方案总报告》§4（VAM-Coder 方案）与 §6（P0 最小原型）实现。
**本阶段只验证工程正确性**：不训练模型、不接入真实 KV 缓存、不产出论文性能数据。

- 实现日期：2026-10-16
- Python：3.12.10（要求 ≥ 3.10）
- 平台验证：Windows（win32）；SQLite 3.49.1

---

## 1. 干净环境运行（一条命令）

```bash
cd D:\Demo\DynaMem\vam-coder && python -m pip install -r requirements.txt && python -m pytest tests/ -v --tb=short
```

期望输出结尾：`23 passed`（实测 2026-10-16：23 passed in 0.91s，退出码 0）。

附：六项必过检查的场景实验（生成实验日志与结果报告）

```bash
python scripts/run_p0_scenario.py
```

期望输出结尾：`ALL PASSED: True`（退出码 0），并生成
`results/p0_scenario_report.json`、`logs/scenario_decisions.jsonl`、
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
├── requirements.txt           # 依赖锁定
├── pytest.ini                 # 测试配置（pythonpath=src）
├── config/
│   └── default.json           # 运行配置（哈希算法/闭包深度/预算/路径）
├── src/vam_coder/             # 源码（与配置/日志/结果分离）
│   ├── models.py              # MemoryEntry / Validity / Action 等数据模型
│   ├── hashing.py             # blake3（可退化 blake2b）
│   ├── config.py              # AppConfig 加载与路由相关字段摘要
│   ├── parser.py              # tree-sitter 符号提取 + 名称依赖消解
│   ├── store.py               # SQLite 静态存储（symbols/dep_edges/repo_state）
│   ├── invalidation.py        # 失效管理器：sync / verify / 依赖闭包 / tombstone
│   ├── router.py              # 规则路由器（四动作 + 预算降级 + 决策日志）
│   ├── logging_util.py        # JSONL 实验日志读写
│   └── pipeline.py            # 流程编排（open_store/sync_repo/route_repo）
├── tests/                     # 单元 + 集成测试（conftest 提供临时仓库夹具）
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
- 依赖提取两趟解析：先收集全部符号，再按名称消解 `call` 边
  （同文件限定名 → 同文件短名唯一 → 全局短名唯一）；歧义/未知记入
  `unresolved_calls`，不猜测。
- **语言限制（明确记录）**：当前仅支持 `.py`。`.js/.ts/.java/.go/.rs/.c/.cpp` 等
  认得出但无 grammar，解析时记入 `skipped_files`（reason=`unsupported_language`），
  有测试覆盖（`test_unsupported_language_recorded`）。
  Python 内部限制：函数内嵌套函数/嵌套类不作为独立符号（其调用计入外层符号）；
  不做完整 import 语义解析。

### 4.2 静态存储 `store.py`（SQLite）
`symbols` 表每行保存（用户要求的必备字段加粗）：
**symbol_id、content_hash、version、deps、summary、validity** + repo_id、file_path、
qualified_name、kind、source_hash、kv_ptr、provenance、size/span、
last_seen_repo_version、updated_at。

- `content_hash`：**记忆建立时的依据**（不被当前源码覆盖，stale 语义由此而来）。
- `source_hash`：最近一次观察到的当前源码哈希（幂等变更检测）。
- `dep_edges`：`depender → dependee` 边索引，与 `deps` JSON 字段同事务维护。
- `repo_state`：仓库级单调版本号（有符号变化才 bump）。
- tombstone 行**保留**（可审计）但 `validity=tombstoned`，默认检索可过滤。

### 4.3 失效管理器 `invalidation.py`（报告 §4.5）
| 规则 | 行为 |
|---|---|
| 源码未变化 | 解析哈希 == `source_hash` → 零状态写入、版本不 bump（幂等，测试 1） |
| 自身内容变化 | `source_hash` 更新、`version+1`、`validity=stale`（测试 2） |
| 源码回退到记忆依据 | 自动恢复 `valid`（`version` 仍 bump） |
| 删除 / 重命名 | 旧 symbol_id → `tombstoned`；重出现则复活并版本接续（测试 4） |
| 依赖闭包传播 | stale∪tombstoned 为种子，反向依赖 ≤ `closure_depth`（默认 2）层 → `unverified`；已是 stale/tombstoned 不覆盖（测试 3） |
| 恢复协议 | `verify(symbol_id)` 重解析重哈希：匹配依据 → `valid`；失配 → `stale`；消失 → `tombstoned`。**sync 不自动治愈 unverified**（保守） |
| 依赖边刷新时机 | 置于闭包传播**之后**，避免重命名时过早清边切断传播路径 |

### 4.4 规则路由器 `router.py`（报告 §4.6 阶段 A，无训练）
逐条目优先级：
1. `tombstoned` → **DROP**（不是有效对象）
2. `stale` / `unverified` → **EXPAND**（**REUSE_KV 被明令禁止**，理由写入日志）
3. 预算超限且有摘要（仅 valid）→ **COMPRESS**
4. `kv_ptr` 可用且 `simulate_kv=true` → **REUSE_KV**
5. 否则 → **EXPAND**

全局预算降级：超预算时按 keep-score = `validity_rank/(est_tokens+1)` 升序逐级降级
（valid：REUSE_KV/EXPAND→COMPRESS→DROP；非 valid：EXPAND→DROP），直到满足预算。
动态层（当前指令/最新报错）保护**不在本阶段范围**（见 §6）。

每次 `route()` 写入 `logs/*decisions.jsonl`：`request_id`（输入内容哈希，可复现）、
预算、总预估 token、配置摘要、每条决策的 **action + validity + est_tokens + reasons**，
并显式声明 `simulated: {kv: true, summary: true}`。

### 4.5 日志 `logging_util.py`
JSONL 追加写：失效事件（`insert/content_stale/content_reverted/tombstone/
dependent_unverified/verify_*/sync_completed`）与路由决策（`route`），
每条都带 `reason` 字段解释“为什么”。

---

## 5. 已实现 vs 模拟（诚实边界）

| 能力 | 状态 | 说明 |
|---|---|---|
| 符号索引、SQLite 存储、哈希/版本失效、依赖闭包、tombstone | **已实现** | 有单元+集成测试 |
| 规则路由器四动作与预算降级 | **已实现** | 有测试；决策日志可解释 |
| JSONL 实验日志、场景实验报告 | **已实现** | `logs/`、`results/` |
| **KV 缓存复用** | **模拟** | `kv_ptr` 形如 `sim://kv/py-model/<hash>`，仅作“可用性标志”参与路由；**不分配、不复用任何真实张量**，无 prefill/显存测量 |
| **COMPRESS 摘要** | **模拟** | 确定性抽取式 stub（docstring/首行），**非模型生成**，无 token 计费 |
| token 估算 | **模拟** | `bytes/4` 粗估，非真实 tokenizer |
| `simulate_kv=false` 行为 | 已实现 | 关闭后 REUSE_KV 不可达，回退 EXPAND（为 P2 真实 KV 留开关） |

---

## 6. 未实现功能与已知缺陷（P0 边界，如实列出）

1. **无真实 KV 分片**（P2）：无 safetensors 落盘、无 vLLM prefix caching、无 prefill/显存实测。
2. **无 LLM 参与**：无摘要生成、无主干推理、无任务成功率/延迟指标（P1/P2）。
3. **无动态层**：路由器只见静态记忆条目，不含“当前指令/最新报错”装配与保护。
4. **无学习式路由器**（阶段 B）与任何训练代码——按要求未实现。
5. **多语言**：仅 Python；嵌套函数不建符号；依赖为名称消解（非完整 import 解析），
   跨文件重名且同文件无唯一匹配时记 unresolved、不建边（可能漏边，不会错边）。
6. **`unverified` 恢复依赖显式 `verify()`**：`sync` 不自动治愈；报告 §4.5 的
   “重哈希后升级”只证明“记忆内容与当前源码一致”，**不验证依赖语义**——
   这是保守设计的已知弱点，P1 需评估是否需要语义级再确认。
7. **回退自动恢复 `valid`** 依据是“内容与记忆依据完全一致”，若外部语义（未入库的
   调用方）已变则仍可能误判——同属闭包覆盖范围问题。
8. **预算 token 为粗估**，COMPRESS/REUSE_KV 的成本模型是规则近似，不等于真实代价。
9. 未接入 git（diff→符号映射用整文件重解析+哈希比较代替 commit 级增量）。
10. **未做**并发/多仓库性能优化；SQLite 单连接、单进程。

---

## 7. 测试与实测结果（2026-10-16，干净环境）

命令：`python -m pytest tests/ -v --tb=short` → **23 passed，退出码 0**
（原始输出：`results/pytest_clean_run.txt`）。

| # | 用户必过测试 | 对应用例（实测结果） |
|---|---|---|
| 1 | 源码未变化时哈希和版本状态保持一致 | `test_unchanged_source_keeps_hash_and_version` **PASSED**；场景 C1 **PASS**（repo_version 1→1，snapshot_equal=True） |
| 2 | 函数内容变化时旧记忆失效 | `test_content_change_invalidates_old_memory` **PASSED**；场景 C2 **PASS**（stale，version 1→2，记忆依据不变） |
| 3 | 依赖函数变化时相关依赖方按规则进入 unverified | `test_dependency_change_marks_dependents_unverified` **PASSED**（d=1 helper、d=2 run、lone 不受影响、helper version 不 bump、verify 可恢复）；场景 C3 **PASS** |
| 4 | 函数删除或重命名时旧符号不能被当作有效对象 | `test_deleted_symbol_tombstoned` + `test_renamed_symbol_tombstoned_and_new_inserted` **PASSED**；场景 C4 **PASS** |
| 5 | 失效记忆不能执行 REUSE_KV | `test_invalid_memories_never_reuse_kv[3 参数化]` + `test_tombstoned_is_not_a_valid_object` **PASSED**（stale/unverified→EXPAND、tombstoned→DROP、valid 对照 REUSE_KV）；场景 C5 **PASS** |
| 6 | 重复执行相同输入结果可复现，日志能解释路由决策 | `test_routing_reproducible_and_logged` **PASSED**（request_id/动作一致、逐条 reasons 非空）；集成 `test_end_to_end_index_invalidate_route`、`test_repeated_sync_and_route_reproducible` **PASSED**；场景 C6 **PASS**（跨运行 request_id 同为 `3b0d4ef6fa0943be`） |

其余覆盖：解析 3 项、存储 3 项、配置 3 项、预算降级 2 项、集成 2 项 —— 合计 23 项，
全部真实执行通过（未通过 0 项）。场景实验报告：`results/p0_scenario_report.json`
（六项 PASS，含环境信息），日志：`logs/scenario_{decisions,invalidation}.jsonl`。

---

## 8. 下一阶段 P1 任务清单（基线复现，对应报告 §6 P1）

> P1 目标：memory-off / symbol+full-read / fixed cache / fixed summary 四基线
> 在同 30–50 任务上的结果表；验收 = 至少一条基线相对 memory-off 有可复现差异。

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
| 查看路由决策日志 | `type logs\scenario_decisions.jsonl` |
| 查看失效事件日志 | `type logs\scenario_invalidation.jsonl` |
| 查看实验报告 | `type results\p0_scenario_report.json` |
