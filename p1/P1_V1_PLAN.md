# P1-v1.0 实施计划与任务集设计（预注册草案）

状态：**设计完成，未实施，未启动正式实验**。
依据：`p1/results/audit_p1_first_run_20261018_123047.md`（首轮审计）、
`p1/results/p1_harness_fixes_20261018.md`（脚手架修复）。
原则：任务与判据先冻结再看结果；不修改冻结 P0（`a31a0c1`）；失败全量保留。

---

## 0. 研究假设与指标（预注册）

**H1（质量-成本权衡）**：在多轮 Python 代码修改任务中，版本感知失效 +
按需路由（vam_coder）相对 memory_off，能在步通过率不显著下降的前提下
降低累计输入 token。

**H2（机制必要性）**：相对 fixed_summary（冻结摘要），vam_coder 在
“过期记忆陷阱”类任务上通过率更高；该差异由失效检测（stale/unverified →
EXPAND）中介。

**非目标**：不主张真实 KV 张量复用/显存收益（REUSE_KV 仍为文本省略代理，
若服务端返回 `cached_tokens` 则单独报告为“服务端前缀缓存命中”，不并入 H1）。

**主指标**（分开报告，禁止互相替代）：
1. 步通过率 / episode 全通过率（隔离 pytest）
2. 累计 prompt tokens、completion tokens（API usage；`raw_usage` 留档）
3. 模型调用时延（中位、p95）与系统开销（sync+route+assemble）
4. 机制量：stale/unverified/tombstone 计数、EXPAND/DROP/REUSE_KV 决策数、
   `reuse_omitted`（并新增“决策级可省略量”与“文件级实际省略量”双计数）

**样本与重复**：每 episode × 基线 × 重复 r∈{1..R}，R=3（资源允许升至 5）；
episode 为统计单元（步不作为独立样本）；报告 bootstrap CI，不做
“p<0.05 即结论”的单一阈值叙事。

---

## 1. 任务集设计：24 个 episode（目录级设计，代码在阶段 A 创建）

约定：每 episode 2 步；`project/` 初始仓库（文件平铺，测试经 PYTHONPATH
导入）；`eval/stepN/` 隐藏测试（模型不可见）；语言仅 Python。

| # | episode id | 类别 | 初始文件（要点） | 步骤指令（摘要） | 成功判据 | 预期失效机制 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `inv_dep_buffer` | 跨文件依赖 | stock.py(available), orders.py(can_fulfill) | s1 修正可售计算；s2 引入 BUFFER 缓冲语义 | step 测试全过 | s2: available stale→can_fulfill unverified |
| 2 | `inv_dep_rounding` | 跨文件依赖 | pricing.py(round), invoice.py(total) | s1 改舍入规则；s2 在 invoice 增加依赖 round 的校验 | 同上 | 依赖闭包 unverified |
| 3 | `catalog_tax_chain` | 依赖链(深度2) | tax.py, item.py, cart.py | s1 改税率；s2 改 cart 汇总依赖 item | 同上 | 深度2 闭包传播 |
| 4 | `api_swap_callsite` | 跨文件调用方 | client.py(fetch), app.py(use) | s1 fetch 改签名(参数序)；s2 修调用方 | 同上 | 被调 stale→调用方 unverified |
| 5 | `sig_kwarg_default` | 签名变化 | core.py(pad, width=2) | s1 默认 width=4；s2 新增调用依赖默认值 | 同上 | 自身 stale |
| 6 | `sig_return_tuple` | 签名变化 | parse.py(split_kv) | s1 返回 (k,v)；s2 更新调用方解包 | 同上 | stale+unverified |
| 7 | `sig_remove_param` | 签名变化 | util.py(fmt, sep) | s1 移除 sep；s2 同步调用方 | 同上 | stale+unverified |
| 8 | `rename_public_fn` | 重命名 | core.compute→compute_double, app.py | s1 重命名；s2 改 helper 偏移 | 同上 | tombstone DROP + caller unverified |
| 9 | `delete_unused_fn` | 删除 | lib.py(used, dead) | s1 删除 dead；s2 新增引用 used 的函数 | 同上 | tombstone；无关符号保持 valid |
| 10 | `rename_method_class` | 重命名(类) | model.py class+method | s1 改方法名；s2 改调用 | 同上 | method tombstone |
| 11 | `dup_name_modules` | 同名消歧 | utils/geometry.py(circle_area), utils/stat.py(circle_area 别义) | s1 修 geometry 版；s2 在 stat 增加同名新函数 | 同上 | 同名不同 file_path 的符号区分 |
| 12 | `shadow_local_global` | 同名消歧 | calc.py 全局 rate + 局部 rate 变量 | s1 改全局；s2 增加依赖全局的函数 | 同上 | 索引按限定名区分 |
| 13 | `import_alias_switch` | 同名/别名 | a.py helper, b.py as h | s1 改 a.helper；s2 把 b 的别名指向新函数 | 同上 | 跨文件别名依赖 |
| 14 | `noop_neighbor_edit` | 无关修改 | main.py, notes_lib.py | s1 只改 main 注释/无关函数；s2 改 notes_lib | 同上 | 无关符号保持 valid→REUSE_KV 可省略 |
| 15 | `unrelated_new_file` | 无关新增 | app.py | s1 新增 unrelated.py；s2 改 app | 同上 | insert 不污染旧条目 |
| 16 | `stale_doc_drift` | 过期摘要陷阱 | price() docstring 写死数值 | s1 只改常量；s2 要求写死当前值 | 同上 | stale→EXPAND（同首轮 trap 结构，换领域） |
| 17 | `stale_formula_drift` | 过期摘要陷阱 | fee() 摘要描述公式 | s1 改公式；s2 内联当前公式 | 同上 | 同上 |
| 18 | `stale_enum_drift` | 过期摘要陷阱 | status 枚举注释 | s1 增删枚举值；s2 依赖新值 | 同上 | 同上 |
| 19 | `closure_two_hop` | 依赖闭包 | low.py→mid.py→high.py | s1 改 low；s2 改 high 依赖 mid | 同上 | 深度2 unverified |
| 20 | `closure_wide_fanout` | 依赖闭包扇出 | hub.py 被 3 文件调用 | s1 改 hub；s2 只改其中一个调用方 | 同上 | 多 dependents 同时 unverified |
| 21 | `reread_after_breaking` | 需重读 | config.py 常量表 | s1 破坏性改表结构；s2 适配消费方 | 同上 | 必须重读才能正确 |
| 22 | `reread_partial_edit` | 需重读 | multi.py 多函数 | s1 只改函数 A；s2 要求基于 A 改 B | 同上 | A stale；B unverified |
| 23 | `tombstone_revive` | 删除后恢复 | core.py | s1 删函数；s2 又要求恢复同名函数 | 同上 | tombstone→复活路径 |
| 24 | `mixed_refactor` | 混合 | 3 文件小重构 | s1 部分重命名；s2 继续重构剩余 | 同上 | 多机制叠加 |

设计约束：
- 每个 episode 的初始仓库 ≤ 4 文件、每文件 ≤ 40 行（控制 8k 上下文与成本）。
- 成功判据全部由 `eval/stepN` 的 pytest 定义；判据不依赖 docstring 文本
  （除非该 episode 的失效机制显式依赖注释漂移，且写入 design_notes）。
- 指令固定文案，禁止按方法结果回调。

## 2. 四组主基线（定义冻结）

| 基线 | 定义（在首轮语义上加固） |
| --- | --- |
| `memory_off` | 每步提供当前全部 `.py` 源码；无 store |
| `symbol_full_read` | 每步提供索引内全部存活符号所在文件全文；无路由 |
| `fixed_summary` | step1 建摘要后冻结；每步只给摘要；**不**随代码刷新 |
| `vam_coder` | 每步 sync→route→按决策装配；REUSE_KV 仅当对话中已有相同 source_hash 内容才省略 |

**历史策略（必须在 v1.0 冻结前做出的唯一设计决定，见阻塞项 B2）**：
首轮四基线均保留多轮对话历史，导致“无记忆”基线仍有隐性源码通道。
候选：(a) 维持现状并声明“记忆比较仅限装配上下文”；(b) 每步无状态重置
（丢历史，REUSE_KV 省略改为跨步工作区快照对比）。(b) 更干净但改变
REUSE_KV 代理语义。**未决前不启动正式实验。**

同一 episode 各方法：相同 project 拷贝、相同指令、相同模型参数、相同
eval；独立 workspace / store / logs（已实现）。

## 3. 消融（与主基线分开报告，仅接口可关时实施）

| 消融 | 实现方式（不动 P0 源码） | 状态 |
| --- | --- | --- |
| `abl_no_invalidation` | 每次 sync 后将全部符号 `set_validity('valid')`（harness 层） | 可行 |
| `abl_no_routing` | 跳过 route，全部按 EXPAND 装配（保留 sync） | 可行 |
| `abl_no_dep_closure` | 配置 `closure_depth=0` 的 AppConfig 副本 | 可行（P0 已支持） |

消融只与 vam_coder 对照，不与四主基线混排；结果分表。

## 4. 正式运行协议

1. 固定：模型精确标签（gguf 文件 sha256 或量化名 q6_k）、llama-server
   版本（`/version` 落盘，已实现探测）、ctx=8192、temperature=0、seed=0、
   max_tokens=1024、budget=4096、硬件记录（GPU 型号/显存）。
2. 每 episode×基线×重复 R=3；**每个 (episode, rep) 轮换基线顺序**
   （脚手架已按 episode 轮换；rep 级再加偏移）。
3. 不同 rep 使用独立 run 目录；禁止复用 workspace。
4. 服务预热：正式 run 前跑固定 3 次预热请求并丢弃（新增 `--warmup N`，
   列为 v1.0 待办）。
5. 命令模板：
   ```bash
   python p1/scripts/run_p1.py --episode all --baselines all \
     --endpoint http://127.0.0.1:8080/v1 --model <tag> --out p1/results/runs/<batch_id>
   ```
   消融：`--baselines abl_no_invalidation,abl_no_routing,abl_no_dep_closure`
   （需先实现，见阶段 A）。

## 5. 数据 schema 与目录规范

沿用现行结构并新增（已在脚手架落地的）：
- `run_meta.json`：tasks/eval/script sha256、server_probe、
  baseline_rotation、p1_untracked_in_git
- `steps/<step>/messages.json`（完整请求）、`result.json.raw_usage`
- per_step.csv 列定义不变；v1.0 增列：`reuse_omitted_decisions`、
  `reuse_omitted_files`、`rep`、`baseline_order_index`

失败分类（评测与运行错误分列）：
`MODEL_NO_EDIT / MODEL_BAD_FORMAT / MODEL_WRONG_SEMANTICS / APPLY_REJECTED /
EVAL_FAIL / MODEL_HTTP_ERROR / HARNESS_ERROR`（分类器在分析脚本中实现，
不修改原始记录）。

## 6. 阶段划分与阻塞项

| 阶段 | 内容 | 退出标准 | 阻塞项 |
| --- | --- | --- | --- |
| A 任务集创建 | 实现 24 episode 的 project/eval | 每个 eval 对“参考补丁”通过、对初始代码失败 | 无（人力） |
| B 冻结 | tasks.json v1.0 + eval 哈希清单 + git 提交 P1 | 哈希与 commit 写入冻结记录 | **B2 历史策略未决** |
| C 基线验证 | 每基线 1 episode smoke + dry-run | 四基线语义核对表全绿 | B |
| D 正式运行 | 24×4×3 = 288 episode-runs | 无 HARNESS_ERROR；原始数据完整 | **B1 服务/硬件元数据确认；B3 重复运行时间预算** |
| E 统计分析 | 预注册指标 + CI + 失败分类 | 分析脚本可从原始目录重算全部表 | D |

**阻塞项清单（启动 D 前必须关闭）**：
- B1：确认正式实验用服务版本与模型哈希，写入 run_meta（探测已实现，
  需服务在线时跑一次校验）。
- B2：历史策略 (a)/(b) 二选一并冻结（影响所有比较的解释）。
- B3：288 runs 的时间/电力预算与是否升 R=5。
- B4：P1 代码纳入 git 分支（当前 `?? p1/`，run_meta 已记录该事实）。

## 7. 本轮明确不做的事

- 不启动任何全量正式实验。
- 不修改冻结 P0。
- 不删除首轮 8 个 run 与审计/修复记录。
- 不在 B2 未决前解释“vam 是否更省 token”为方法结论。
