# V12-F 独立任务集确认性实验预注册（Part3）

版本：**v1（冻结）**
日期：2026-11-07（起草并冻结）
状态：**已冻结。任何修改 = 版本号 +1 + 变更记录；sha256 见 `p1/experiments/independent_validation/prereg_freeze.json`。冻结先于任何本任务集的确认性模型请求。**

与 P1 预注册（`v12f_validation_preregistration.md`，sha `088898a3…`）的关系：**除本文件明示的差异项外，全部沿用 P1 冻结口径**（解码参数、成功判定、错误分类、排除规则、Bootstrap、主检验、NA 规则、非劣界值）。差异项集中在 §3。

---

## 0. 研究问题（总任务书 RQ1–RQ5 在本实验中的落点）

| RQ | 内容 | 本实验角色 | 主指标 |
| --- | --- | --- | --- |
| **RQ1** | V12-F 是否在独立任务集上继续降低 Prompt Token 开销 | **确认性（本实验）** | prompt_tokens/episode（task 级配对差 + 95% CI） |
| **RQ2** | 开销降低后能力是否满足预注册非劣效 | **确认性（本实验）** | ESR（task 级配对差 + 95% CI，非劣界 −12pp） |
| **RQ3** | P2 消融 + VSO 专项能否共同支持 VSO 独立机制贡献 | 综合判定（**不产生新数据**；证据=P2 消融 + VSO Phase1/2） | O′/redact 消融差值、VSO UOR/SOR/FBR/FSR/EDR |
| **RQ4** | P1 与独立任务集结果是否一致 | 一致性比较（本实验 vs P1 冻结结果） | RQ1/RQ2 效应量方向与量级；**同模型（deepseek）内比较，禁止跨模型合并绝对 token/ESR** |
| **RQ5** | 当前证据是否足以支持论文核心创新主张 | 综合判定（审计+本实验+文献） | 逐主张证据表（支持/部分/不支持） |

## 1. 主要假设（冻结；判定规则开跑前锁定）

- **H1（RQ1 主）**：`vam_coder_v1.2_F` 的 prompt_tokens/episode 低于 `memory_off`（task 级配对差 < 0，双侧 sign-flip + 95% CI 不含 0；Holm 校正见 §6）。
- **H1′（RQ1 次）**：`vam_coder_v1.2_F` 低于 `symbol_full_read`（同上）。
- **H2（RQ2 主）**：`vam_coder_v1.2_F` − `memory_off` 的 ESR 配对差的 95% CI 下界 ≥ **−12pp**（非劣通过）。
- **H2′（RQ2 次）**：`vam_coder_v1.2_F` − `symbol_full_read` 同上。
- **不做**：ESR 优效主张（P0 功率分析结论沿用）；KV 显存主张（无张量实测）；双 Token 独立收益主张（专项未完成）。
- 证据链要求与 P1 相同：① 效应量+CI；② 非劣界内；③（机制归因引用 P2，不要求本实验重复消融）。

## 2. 任务集与规模

| 项 | 值 |
| --- | --- |
| 任务集 | `p1/tasks_independent_v1/`（Part2 设计：`docs/independent_taskset_design.md`） |
| 任务数 | **48** = short 16（2 步）+ medium 16（5 步）+ long 16（10 步）；步总数 **272** |
| 独立性 | 24 archetype（非 P1 的 8 族换皮）；与 v1/holdout/P1 指令包含=0、文件 sha 交集=0、禁词=0；泄漏审计见设计文档 §6 |
| 信息点 | 每题预声明 `required_info_points`（实验前冻结，禁止事后改） |
| 冻结物 | `independent_tasks.json` + `independent_tasks_manifest.json`（全量哈希+校验记录）；freeze-once |
| 架构 | **A** `vam_coder_v1.2_F` / **B** `memory_off` / **C** `symbol_full_read`（与 P1 完全一致） |
| 重复 | R=5 → 48×3×5 = **720 episodes**；请求数 = 272×3×5 = **4080** |

**任务建设与冻结顺序**：本预注册冻结（记录本档 sha）→ 任务集生成校验通过并冻结（manifest 记录本档 sha）→ 才允许任何确认性模型请求。

## 3. 与 P1 的差异项（仅此清单，其余全部沿用）

| 项 | P1 | 本实验 |
| --- | --- | --- |
| 任务集 | tasks_p1_validation（8 族参数化） | tasks_independent_v1（24 archetype） |
| 随机化 seed | 20261107（P2=…08，P3A=…09，双Token=…10） | **20261111**（开跑前写入 run_meta；仅打乱 episode 顺序，任务内配对保持） |
| S5 token 上限 | 按 dry 估算×2 | **6,000,000**（依据：P1 实测 2.80M ×2 并取整；超出即停并报告） |
| 就绪门（smoke） | P0 系列 | 见 §8：首批 36 集后地板/天花板/protocol 检查（只停不调） |

## 4. 模型与配置（冻结）

| 项 | 值 | 理由 |
| --- | --- | --- |
| 主模型 | `deepseek-v4.1-flash-1017` @ `https://maas.qianwenaiapi.com/compatible-mode/v1` | 与 P1/P2 同款：结果可比（RQ4）；P3A 已证方向跨模型一致；成本可控；P1 上 ESR 非地板 |
| 鉴权 | 环境变量 `VAM_API_KEY`（不写入产物） | 既有方式 |
| 解码 | temperature=0, seed=0, max_tokens=**2048**, history_policy=keep | P1 冻结值；2048 来自 P0 exp6 判定（最小无触顶预算） |
| SYSTEM_PROMPT sha256 | `4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a` | 与 P1 相同 |
| build_messages sha256 | `f0b477b0046282739ba1309e5035b2beb2f2f8d2564535d7154019a9aee9e436` | 与 P1 相同 |
| p1_common sha256 | `b6ce07a3bccbcb20fe94e8346fff0b7d8f55b6dea5fc0356da3b15c26e88a9b6` | 与 P1 相同 |
| runner | `run_p1_v12.py`（sha `19fd9669…`，含 P2 三开关，默认值=冻结配置） | 生产代码零修改 |
| Bootstrap | seed=**20261102**, B=10000, 聚类 task_id | P1 冻结值 |
| 成功判定 | episode 全部步 eval_success=1 | P1 冻结值 |

## 5. 运行、记录与失败分类（冻结）

- **顺序**：randomization seed=20261111 打乱 episode 顺序；同一 task 的三臂×五重复作为配对单元保持可聚合。
- **断点续跑**：orchestrator 按 execution_log 跳过已 OK 集；半成品 runner_out 先 resume-cleanup 再重跑（P2 已验证的补丁，必须带）。
- **必须保留**（总任务书 Part5）：初始仓库、每轮最终 messages、请求/响应记录、token 统计、系统决策与检索记录、文件变更与测试结果、失败原因、每集 run_meta。
- **错误分类**（rev3 §4.5，沿用）：protocol / architecture / task / infrastructure。protocol（含触顶/空响应）**计入 ESR 失败，不事后剔除**；architecture 缺陷 → 停机报告；infrastructure 单集失败 → 保留记录并按 §7 处理。
- **排除规则**：无事后排除。仅允许：infra 全轮失效整轮重跑（记审计）；除此之外任何样本不得删除。

## 6. 统计分析计划（冻结）

- **统计单位**：task_id（重复在 task 内聚合；任务族=24 archetype 作敏感性聚类）。
- **主检验**：task 级配对 sign-flip 置换（双侧 α=0.05）；二元附 McNemar（敏感性）；连续 token 附 Wilcoxon（敏感性）。
- **区间**：task-cluster bootstrap（seed=20261102, B=10000）95% CI。
- **多重比较**：预指定两条主比较 `A−B`、`A−C`，RQ1 与 RQ2 **各做一次 Holm 校正**（α=0.05）；其余（按难度分层、按 archetype、P1 对比）标注次要/探索。
- **报告**：每格 mean/sd/median/IQR/95%CI + 配对效应量（绝对+相对%）；**效应量与 CI 为主，p 为辅**；难度分层（short/medium/long）与族敏感性（24 archetype 聚合）必报；失败任务全量披露。
- **NA 规则**：零成功臂 TPSE=NA（不记 0）+ na_ratio；非适用字段=NA（≠0）。
- **RQ4 一致性口径**：同为 deepseek，比较**相对降幅与方向**（如 prompt −x% vs P1 的 −23.6%）；禁止把两任务集的绝对 token 或原始 ESR 直接合并成一个样本。
- **判定用语**：统计显著、效应量、工程意义分开写；不支持的假设如实写"不支持"，不得重包装。

## 7. 缺失数据与基础设施失败（冻结）

- 单集 infra 失败（网络断连、服务 5xx 等）：记录 rc 与日志，**该集重跑一次**；重跑仍失败 → 该 task×arm×rep 记为缺失，分析时该配对单元内成对删除（pairwise），披露缺失数与分布。
- 禁止把 infra 失败计为模型 ESR 失败，也禁止把模型失败改记 infra。
- 与 protocol 的边界：响应非空但触顶/空截断 → protocol（计 ESR 失败）；请求未到达/连接层错误 → infra。

## 8. 就绪门与提前停止（冻结）

1. **就绪门（smoke）**：全量开跑后前 **36 集**（每臂 12 集）完成时检查：
   - 三臂 ESR 若**全为 0 或全为 1**（完全地板/天花板）→ **停止并报告**（不改题、不换口径、不扩预算）；
   - protocol 违规率 >20% → **停止并报告**（预算/格式问题，处置方案另行获批）；
   - 任一臂 infra 失败率 >20% → **停止并报告**。
   通过则继续至完成。就绪门只读不调。
2. **S5**：累计 token > 6,000,000 → 停止，已写数据保留，报告完成比例。
3. **生产代码缺陷**（总任务书硬约束）：发现即停止受影响实验，记录问题与影响范围，**不得擅自修复后混合统计**；修复方案需单独报告并重新审查协议。
4. **冻结矛盾/数据完整性问题**：同上，停下报告。

## 9. 成本估算（冻结）

- 请求数：272 步 ×3 臂 ×5 = **4080**（与 P1 相同）。
- Token：按 P1 实测 2.80M 外推 ≈ **2.8M**（任务步数同构）；S5=6M（2× 取整）。
- 时长：按 P1/P3A 实测速率 ≈ **6–9 小时**（后台断点续跑）；期间并行的双 Token 专项（若未完成）将争用同一端点——**实施时二者串行或错峰**，避免互相触发限流。
- 模型费用：沿用既有端点配额；无新模型、无新付费服务。

## 10. 冻结清单（本档冻结时逐项钉 sha）

1. 本预注册文档 sha256；
2. 任务集 `independent_tasks.json` / `independent_tasks_manifest.json` sha256（任务集冻结时回填至 manifest 的 `prereg_sha256`）；
3. 设计文档 `independent_taskset_design.md` sha256；
4. 生产代码哈希（§4 表）；
5. 统计脚本（Part5 分析脚本在开跑前冻结并记 sha；分析只读 execution_log 与 runner 输出）。

## 11. 变更记录

| 版本 | 日期 | 变更 | sha256 |
| --- | --- | --- | --- |
| v1 | 2026-11-07 | 冻结（sha 见 prereg_freeze.json） | 见 freeze 记录 |
