# V12-F 验证程序预注册（VAM-Coder Validation Preregistration）

版本：**v1（用户确认，冻结）**  
日期：2026-11-03（起草）/ 2026-11-04（冻结）  
状态：**已冻结。任何修改 = 版本号 +1 + 变更记录；sha256 见 `p1/experiments/validation_p0/prereg_freeze.json`。**

---

## 0. 决议与范围

**决议一（V13 线降级）**：基于 round1–3 数据，`vam_coder_v1.3_V13A` 规则已否定；`vam_coder_v1.3_V13B` 的唯一差异化机制 no-body→NONE 在 round3 被 v13_I02 因果证伪（省 ~24 tok/步损失 2/24 episode）。**V13 线停止作为主线升级**；`vam_coder_v1.3_V13B` 保留为消融/反例臂，代码不删。

**决议二（主线）**：验证对象为 **`vam_coder_v1.2_F`**（相关文件全量注入），对照为 `memory_off` 与 `symbol_full_read`（非 VAM 架构）。`vam_coder_v1.2_E` 保留为消化（digest）机制对照，进入消融批次。

**范围**：本预注册覆盖批次 P0–P3（见 §3）。不覆盖：V14（补丁协议 / 修复闭环）——单独立项预注册。

## 1. 研究问题（论文主张收敛为三 RQ）

| RQ | 要证明的内容 | 主指标 | 次指标 |
| --- | --- | --- | --- |
| **RQ1 效率** | `vam_coder_v1.2_F` 减少上下文开销 | prompt_tokens/episode（配对差） | total_tokens、completion_tokens、LLM 请求数、耗时 |
| **RQ2 能力保持** | 减少上下文不造成不可接受的能力损失 | ESR（配对差 + 95% CI） | SPR、失败类型分布、回归（全步 eval） |
| **RQ3 机制有效性** | 效率收益来自结构化索引与选择性注入，而非任务简单/随机性 | 消融差值（配对） | 关键信息遗漏率（CMR）、无关读取率（IRR）、错误传播率（MEPR） |

**证据链要求**（三条同时成立才允许写"有效"）：① 资源下降有效应量与 CI；② 能力损失不超过预设边界；③ 消融显示收益随机制移除而消失。

## 2. 冻结项（任何批次不得更改；更改 = 新版本预注册 + 审计记录）

| 项 | 冻结值 |
| --- | --- |
| 主模型 | `deepseek-v4.1-flash-1017` @ `https://maas.qianwenaiapi.com/compatible-mode/v1`（调用日期写入各轮 run_meta） |
| 异族模型（P3 候选） | 端点在列：`qwen3.8-flash` 或 `glm-5.3`（启动前在预注册补记中指定其一，禁止看结果后挑选） |
| 能力边界模型 | Qwen2.5-Coder-1.5B-Instruct Q6_K（本地 llama-server；**不与云端合并计算**） |
| SYSTEM_PROMPT sha256 | `4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a` |
| build_messages sha256 | `f0b477b0046282739ba1309e5035b2beb2f2f8d2564535d7154019a9aee9e436` |
| p1_common sha256（含可选鉴权头） | `b6ce07a3bccbcb20fe94e8346fff0b7d8f55b6dea5fc0356da3b15c26e88a9b6` |
| 解码参数 | temperature=0, seed=0, history=keep(24000), closure_depth d=2, K_max=8 |
| 输出预算 | P0 敏感性轮 {1024,2048,4096}；**P1 主预算 = P0 判定规则选出的最小无触顶预算**（§7 实验6） |
| Bootstrap | seed=**20261102**, B=10000, 聚类单位 task_id；TPSE 零成功=NA 并报告 na_ratio |
| 每轮随机化 seed | 每轮新值、开跑前写入 run_meta（round1=20261103, round2=20261104, round3=20261105, 后续轮顺延）；仅打乱 episode 顺序 |
| 成功判定 | episode 全部步 eval_success=1；评测为冻结 holdout 的 pytest 行为断言 |
| 任务冻结 | `p1/tasks_v13_holdout/`（sha 59cebdd9…/manifest fcb8762f…）内容零改动；P1 新任务集按 §5 配额创建后**先冻结后运行** |
| 错误分类 | rev3 §4.5 四类：protocol / architecture / task / infrastructure；**protocol 计入 ESR 失败，不事后剔除**；architecture 必须 S1 停机 |
| 排除规则 | **无事后排除**。仅允许的排除：预注册中明示的 infra 全轮失效（整轮重跑须记审计）；任何触顶/空响应按 protocol 计 |

## 3. 批次总览（探索性 / 确认性分栏）

| 批次 | 内容 | 性质 | 状态 |
| --- | --- | --- | --- |
| **P0** | 本预注册 + 功率分析 + 实验6（max_tokens 敏感性） | 探索性（配置选择与效度） | 本文档起草即启动 |
| **P1** | 实验1 扩任务集主实验 + 实验5 难度分层并入 | **确认性（论文主表）** | 待 P0 完成 + 本档冻结 |
| **P2** | 实验2 机制消融 + 实验3 关键信息保留（CIRE） | 确认性（机制归因） | 待 P1 |
| **P3** | 实验4 跨模型泛化 + 实验7 集内记忆污染 | 确认性/边界声明 | 待 P1–P2 |

**统计功效边界（引自 `validation_p0/power_analysis.csv`，round3 task 级数据模拟）**：

- **Token 差异**：N=40 任务 × R=5 时，`vam_coder_v1.2_F` vs `memory_off`（Δprompt −121.5）与 vs `symbol_full_read`（−134.0）的检出功效 **≥0.99**；vs `vam_coder_v1.2_E`（+39.2）功效 0.99。
- **ESR 差异**：8.3pp 的差值在 N=50×R=5 下功效仅 **0.33**（round3 的任务集中型结构）；齐性效应假设下 MDE=8pp。**结论：可行样本量下不做 ESR 优效主张**；RQ2 以配对差 + 95% CI + **非劣边界 ±12pp**（margin 依据：MDE 量级与 P1 成本的折中，开跑前可改一次并记版本）表述。
- Null 对照（Δ=0 的 pair）假阳性率 ≈ α，模拟管线自检通过。

## 4. 主实验配对与统计计划（全部批次通用）

- **配对单位 = task_id**：同任务同初始快照在各架构下配对运行；分析在 task 级聚合。
- **主检验**：task 级配对 sign-flip 置换（双侧 α=0.05）；二元结果附 McNemar（敏感性）；连续 token 附 Wilcoxon 符号秩（敏感性）。
- **区间**：task-cluster bootstrap（seed=20261102, B=10000）95% CI。
- **多重比较**：主要比较**预指定两条**——`vam_coder_v1.2_F` − `memory_off`、`vam_coder_v1.2_F` − `symbol_full_read`（Holm 校正 α=0.05）；其余比较标注为次要/探索。
- **报告**：每格均值、sd、中位数、IQR、95% CI、配对效应量（绝对差 + 相对 %）；**以效应量与 CI 为主，p 值为辅**。
- **NA 规则**（冻结）：零成功臂 TPSE=NA（不记 0），报告 na_ratio；非适用字段=NA（≠0）。
- **R≥5 的实质**：temperature=0 下同 prompt 仍存在服务端生成非确定性（round2/3 实测），"独立重复"=采样重复；预注册如实披露，不声称确定性解码。

## 5. 实验1 + 实验5：扩任务集主实验（P1，确认性）

| 项 | 方案 |
| --- | --- |
| 任务数 | **48**（40–50 区间内；创建后冻结） |
| 难度分层（并入实验5） | Short 1–3 步 ×16 / Medium 4–8 步多文件 ×16 / Long 9–15 步回溯 ×16；配额**写任务前**固定 |
| 架构 | 3：`vam_coder_v1.2_F`、`memory_off`、`symbol_full_read` |
| 重复 | R=5 → 48×3×5 = **720 episodes**（请求数 = Σsteps×5，Long 轮数多，开跑前按 dry-run 估请求数与 token 并写入 run_meta） |
| 顺序 | 每轮新 randomization seed（开跑前声明），任务内配对保持 |
| 主分析 | RQ1：prompt/episode 配对差 + CI（主表）；RQ2：ESR 配对差 + CI + ±12pp 非劣表述 |
| 曲线分析（实验5） | 每轮 prompt_tokens 轨迹：按 step 序号对齐绘制架构均值曲线（上下文增长速度），配对差按 step 分层 |
| 成本上限 | 开跑前 dry-run 估算 ×2 写入 S5；超出即停并报告 |

**任务建设规则**：与现有 holdout 文件 hash 交集=0；指令零逐字复用；每任务预声明"必要信息点清单"（供实验3 CMR 复用）；eval 行为断言；初态必败/参考解必过验证后冻结。

**任务集构造披露（冻结前补充）**：48 题由**参数化任务族**构建（Short/Medium/Long 各含若干族；同族变体共享结构、不同领域词汇与数值参数）。主分析仍按预注册以 **task_id 聚类**；另报告**按族聚合的敏感性分析**（同族变体视为相关单元时结论是否翻转），并在局限中披露有效独立设计数 < 48。

## 6. 实验2：机制消融（P2）——按 harness 真实开关重映射

| 组 | 配置（单开关） | 验证目的 |
| --- | --- | --- |
| 主实验 | `vam_coder_v1.2_F`（完整） | 基准 |
| 消融-1 | `non_target_related=digest`（=`vam_coder_v1.2_E`） | 全量注入的贡献 |
| 消融-2 | `non_target_related=none`（H 形态） | 相关注入整体的贡献 |
| 消融-3 | `must_full_dep_closure=False` | 依赖闭包的贡献 |
| 消融-4 | `o_prime=False` | 历史复用省略的贡献 |
| 消融-5 | `history_policy=redact` | 完整历史的贡献 |
| 反例臂 | `vam_coder_v1.3_V13B` | 过度优化（no-body→NONE）的代价 |
| 交互 | 消融-1 + 消融-3（同时移除） | 索引×闭包协同 |

**原则**：一次只改一个字段；prompt 模板、预算、模型、R 全部不变。  
**范围声明**：`ReAct+Full History`、`ReAct+Summary/RAG` 基线在本 harness **未实现**（无 ReAct 循环、无跨集记忆写入）——归入 V14 立项，不冒充现有能力。

## 7. 实验6：max_tokens 敏感性（P0，探索性——配置选择）

| 项 | 方案 |
| --- | --- |
| 预算档 | 1024 / 2048 / 4096（全架构同预算；禁止对主架构单独加预算） |
| 规模 | 5 架构 × 12 任务 × **R=1** × 3 档 = 180 episodes |
| 记录 | 触顶（completion==budget）、空响应、protocol 违规、ESR、prompt/completion tokens、失败分类 |
| **判定规则（开跑前锁定）** | **P1 主预算 = 使全部架构 protocol(触顶类) = 0 的最小预算**；若 4096 仍触顶 → 升 8192 重跑本实验并记审计 |
| 性质 | 选择配置的探索性实验；**不得**用其 ESR 差异做架构主张 |

## 8. 实验3：Critical Information Retention Evaluation（P2）

**信息四类**（任务清单预声明，每任务标注其必要信息点类别）：实现体 / 接口签名 / 关键数据（常量·配置·枚举·路径）/ 历史结论（集内多轮）。  
**交付四策略**：FULL / SUMMARY(=digest 形态) / SELECTIVE(按相关性) / OMIT——由消融-1/2/4 与主实验组合实现，不新造注入器。

**指标（分母与单位开跑前锁定）**：

| 指标 | 定义 | 统计单位 |
| --- | --- | --- |
| **CMR** 关键记忆召回率 | 成功送达的必要信息点数 / 该步预声明必要信息点总数 | 步 |
| **IRR** 无关读取率 | 注入的非必要信息单元数 / 注入总信息单元数（单元=文件，行级另报） | 步 |
| **MEPR** 错误记忆传播率 | 被后续步引用的错误信息点数 / 注入的错误信息点数（错误注入=实验7 的受控污染） | 步序列 |

判定规则：信息点"送达"= 其值出现在该步 user.context 全文（可自动检索）；"引用"= 模型输出（FILE 块或中间文本）包含该错误值。允许结论为"V12-F 在某信息类不占优"。

## 9. 实验4：跨模型泛化（P3）

- 主模型结果（deepseek-v4.1-flash-1017）与异族模型结果**分表报告**：ESR、prompt/completion/total、请求数、失败类型；只比较**架构间相对收益的方向一致性**，不合并原始成功率。
- 1.5B 本地模型作为能力边界单列（round1–2 已有，可复用为边界参考，不入主表）。
- 模型 id、API 参数、调用日期写入 run_meta。

## 10. 实验7：记忆污染与冲突（P3，集内版 + 边界声明）

- **可做（集内，history=keep）**：M1 正确记忆复用 / M2 过期结论（第 1 步结论与第 3 步新要求冲突）/ M6 无关记忆干扰——在多步任务内受控构造，预声明污染点。
- **边界声明（不做或仅描述）**：M3/M4/M5 的跨集版本——**V12-F 无跨 episode 记忆写入、无版本控制**；如实写为架构覆盖边界，**禁止**为实验临时加机制后仍称"原始 V12-F"。

## 11. 变更流程

1. 冻结后任何修改 → 版本号 +1 + 变更记录（保留原文），区分探索性/确认性。  
2. 中途发现的缺陷 → 记录、继续或按预声明停机条件停止；禁止按中间结果调任务、预算或判定规则。  
3. 与历史轮（round1–3）的关系：round1–3 定位为**探索性**（其数据用于本档假设生成与功效估计），**不得**与 P1 确认性数据合并计算主效应。

## 12. 关联产物

- 功率分析：`p1/experiments/validation_p0/power_analysis.py` / `power_analysis.csv`
- 历史探索轮：`v13_holdout_validation/`（round1）、`v13b_holdout_validation/`（round2）、`round3_deepseek_flash/`（round3）
- max_tokens 轮：`p1/experiments/validation_p0/exp6_max_tokens/`
