# Part2 独立任务集设计（independent-v1）

状态：设计稿（冻结前）。冻结后本文件与 `tasks_independent_v1/` 清单一并钉 sha，任何模型请求之前完成。

## 1. 动机与要解决的问题（对应审计 D8）

P1 确认性任务集（`tasks_p1_validation`）的已披露弱点：

- 仅 **8 个参数化族**（4 short + 2 medium + 2 long）；同族变体共享同一骨架，只改标识符与数值。有效独立设计数 ≈ 8，而非 48。
- 步语义单一：全部是"指令精确复述改法 → 应用修改"的处方式编辑。
- 仓库形态单一：单层平铺 `.py` 模块、函数式风格、无配置/数据/文档文件参与信息承载。
- eval 形态单一：函数行为断言。

本任务集（Part2）必须在**结构层面**独立于 P1，而不是 P1 的换皮复刻；同时**不得为 V12-F 刻意设计**（既不为记忆臂放水，也不为基线臂挖坑）。

## 2. 结构差异论证（与 P1 的对照）

| 维度 | P1（tasks_p1_validation） | Part2（tasks_independent_v1） |
|---|---|---|
| 独立骨架数 | 8 族 | **24 个 archetype**（short/medium/long 各 8） |
| 变体数/骨架 | 4–8 | 2 |
| 步语义 | 处方式编辑（单一） | 症状诊断修复、契约变更、重构搬迁、规格检索、示例驱动、配置/模式演进、策略变更、状态机演化…… |
| 仓库形态 | 单层平铺模块 | 多目录包、类层级、JSON 配置与数据文件、README/文档作为规格载体、跨文件集成 |
| eval 形态 | 函数行为断言 | 行为断言、异常/边界断言、结构断言（旧符号清零）、跨模块集成断言、配置/数据往返断言 |
| 信息点承载 | 指令 + 工作区 | 指令 + 工作区 + README/docstring/配置文件（多载体） |
| 与 v1/holdout/P1 的指令复用 | —（校验对 v1+holdout=0） | 对 **v1 + holdout + P1 全集** 指令包含关系 = 0，文件 sha 交集 = 0 |

结论：Part2 在骨架数（24 vs 8）、步语义、仓库形态、eval 形态、信息载体五个维度结构性不同；并以机器可检的哈希/指令零交集保证不复用既有题目。

## 3. 配额与规模（与 P1 对齐，保证可比）

- 48 题 = short 16（2 步）+ medium 16（5 步）+ long 16（10 步）；步总数 272。
- 架构（确认性三臂）：`vam_coder_v1.2_F` / `memory_off` / `symbol_full_read`；R=5 → 720 集 / 4080 步请求（与 P1 同量级）。
- 模型、预算、统计口径沿用 P1 冻结设置（deepseek-v4.1-flash-1017、max_tokens=2048、temperature=0、bootstrap seed=20261102/B=10000/cluster=task_id、非劣界 −12pp）；具体以 Part3 预注册为准。
- 任务 ID：`ind_S01a/b … ind_M01a/b … ind_L01a/b`；族字段 = archetype（族敏感性分析按 24 骨架聚类）。

## 4. Archetype 目录（24 骨架）

### Short ×8（每骨架 2 变体，2 步/题）

| archetype | 语义 | 结构要点 |
|---|---|---|
| `ind_short_bugfix` | 症状式 bug 修复 + 边界补修 | 指令给症状不给改法；step2 追加相关边界 |
| `ind_short_config` | JSON 配置与读取器协同演化 | 配置文件 + loader；信息点在配置值 |
| `ind_short_refactor` | 跨文件符号重命名/搬迁 | 行为不变；eval 含旧符号清零断言 |
| `ind_short_specdoc` | 规格在 README，指令只指路 | 信息点载体=工作区文档（非指令） |
| `ind_short_excep` | 异常契约按 README 规格实现 | 抛出类型/时机由文档规定 |
| `ind_short_examples` | 示例驱动实现 | 指令给 I/O 示例对，实现由示例归纳 |
| `ind_short_repr` | 内部表示替换、API 不变 | 重构语义 + 行为回归 eval |
| `ind_short_format` | 文本解析/格式化 | 编解码往返 eval |

### Medium ×8（每骨架 2 变体，5 步/题）

| archetype | 语义 | 结构要点 |
|---|---|---|
| `ind_med_bugchain` | 关联 bug 链逐个修复 | 每步一个症状，共享根因面 |
| `ind_med_schema` | JSON 数据模式 v1→v2 迁移 | loader/writer/consumer 三方同步 |
| `ind_med_state` | 状态机递进演化 | 状态/守卫/转移逐步添加与改约 |
| `ind_med_cache` | 缓存策略演进 | 容量→淘汰→统计→TTL 策略变更 |
| `ind_med_hierarchy` | 类层级语义变更传播 | 基类语义改 → 子类适配 → 新子类 |
| `ind_med_parser` | 解析器文法扩展 | token/错误处理/文法增量 |
| `ind_med_pipeline` | 多阶段数据管道 | 阶段增删 + 配置驱动 + 汇总 |
| `ind_med_registry` | 注册表/分派增长 | 注册→分派→全局策略变更 |

### Long ×8（每骨架 2 变体，10 步/题）

| archetype | 语义 | 结构要点 |
|---|---|---|
| `ind_long_scheduler` | 调度器/优先级队列系统演进 | 排序→ tie-break→策略变更→边界 |
| `ind_long_ledger` | 记账/计费引擎演进 | 档位→窗口→规则二次变更（过期传播） |
| `ind_long_warehouse` | 库存预留/回补系统 | 预留→释放→缺货→策略改约 |
| `ind_long_undo` | 命令日志与回滚系统 | 应用→回滚→压缩→语义改约 |
| `ind_long_graph` | 图结构与遍历语义演进 | 无向→加权→有向→遍历规则变更 |
| `ind_long_protocol` | 消息协议版本协商 | v1/v2 格式→兼容层→字段演进 |
| `ind_long_repo` | 仓储层查询与约束演进 | 查询→索引→约束变更→迁移 |
| `ind_long_plugin` | 插件注册与命令分派系统 | 注册→分派→别名→全局策略 |

设计原则：每个骨架来自常见软件工程请求类型（修 bug、重构、迁移、演进），**不从 V12-F 的机制反推**；同骨架两变体在标识符、数值、控制流细节、辅助文件上均不同（非纯换名）。

## 5. 必要信息点（预声明）

- 每题 2–5 个 `required_info_points`，字段与 P1 同构：`id / type / value / locator / needed_by_steps / redundant_in_instruction`。
- type ∈ {implementation, interface, critical_data, history}。
- 平衡原则（防为记忆臂设计）：`redundant_in_instruction=true`（指令已复述）与 `false`（须从工作区/历史携带）两类都必须存在；history 型信息点来自"后续步骤引用先前已定决策"这一自然演进结构，**不通过刻意扣留真实请求本会给出的信息**制造。
- 每题至少 1 个信息点的载体不在指令里（工作区文件/历史），至少 1 个在指令里——保证三臂在"信息可得性"上同起跑线（差异只来自表示与交付机制）。

## 6. 防泄漏 / 独立性审计（冻结门）

1. **术语泄漏**：全部指令与项目文件 grep 禁词 = 0：`memory|上下文|记忆|复用|reuse|context window|REUSE_KV|symbol_full|memory_off|V12|V12F`（大小写不敏感；中文词全串）。
2. **跨集复用**：对 v1（`tasks/tasks_v1.0.json`）+ holdout + P1 全部指令做包含关系检查 = 0；对三集全部文件（除 .json）做 sha256 交集 = 0。
3. **集内唯一**：48 题指令全集无重复、无包含。
4. **臂公平**：三臂收到完全相同的任务、指令、初始工作区与 eval；臂间唯一差异是表示与交付机制（P1 既定协议）。任务内容不出现任何臂专属提示。
5. **不为结果调题**：冻结在任何本集模型请求之前；冻结后不改题。若冻结后 smoke 揭示 ESR 地板/天花板，按预注册的停止规则报告，不换题。

## 7. 校验管线（生成即验证，任一失败不冻结）

沿用 P1 `make_p1_tasks` 的验证并加强：

1. 每步 eval 在 `ref_{i-1}` 必失败、在 `ref_i` 必通过（判别性）；
2. `parse_edit_targets` 解析出的编辑目标 == 预声明 `expect_targets`；
3. 信息点结构合法（步号范围、type 枚举、布尔字段）；
4. 文件 sha 交集（v1 ∪ holdout ∪ P1）= 0；
5. 指令包含关系（v1 ∪ holdout ∪ P1）= 0；集内唯一；
6. 禁词扫描 = 0；
7. 配额/步数断言：48 题、16/16/16、2/5/10 步；
8. 物化树与 manifest 哈希逐文件一致（materialize 复核）；
9. freeze-once：manifest 存在即拒绝重生成。

## 8. 运行时兼容

- 消费接口与 P1 相同（`run_p1_v12.py --tasks-json <本集>.json`）：episode 需 `id`、`steps[{id,instruction,eval}]`；工作区来源 `<task>/project/`，eval 目录 `<task>/eval/stepN/test_behavior.py`（pytest，`PYTHONPATH=workspace`）。
- Part4 orchestrator 只改任务路径与冻结哈希常量，不改 runner/系统提示/装配逻辑（生产代码零修改）。

## 9. 冻结产物

- `tasks_independent_v1/independent_tasks.json`（题目+信息点）
- `tasks_independent_v1/independent_tasks_manifest.json`（全量哈希+校验记录+审计结果）
- `tasks_independent_v1/` 物化树（project/eval/reference ×48）
- 本设计文档 sha 记入 manifest

## 10. 风险与披露

- 难度无法在冻结前用真实模型校准（冻结须先于任何本集请求）；缓解：步数/风格与 P1 对齐（P1 在同模型上非地板），Part4 首批 smoke 按预注册停止规则处理地板/天花板。
- 同骨架 2 变体仍相关：族敏感性分析按 24 archetype 聚类披露（有效独立设计数下界=24，上界=48）。
- 生成式题面可能有歧义：靠"eval 判别性 + 目标解析 + 参考解全过"三重离线验证兜底。
