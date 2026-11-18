# 预注册补记：V13B(ICG) DeepSeek 确认性实验

版本：**v1（冻结）**  
日期：2026-11-09（起草）/ 2026-11-09（冻结）  
状态：**已冻结。任何修改 = 版本号 +1 + 变更记录；sha256 见 `p1/experiments/v13b_deepseek/prereg_freeze.json`。冻结先于任何本实验确认性模型请求（含冒烟）。**  
用户确认：**「冻结」（2026-11-09，会话书面确认）**  
与主预注册关系：除本文件明示差异外，**沿用** `v12f_validation_preregistration.md`（sha `088898a3…`）与 `v12f_independent_validation_preregistration.md`（sha `7023da82…`）的解码、成功判定、错误分类、排除、Bootstrap、非劣界口径。

---

## 0. 背景与本实验要回答什么

| 已有证据 | 不得迁移的主张 |
| --- | --- |
| V12-F P1/P2：prompt −23.6%/−24.2%，O′ −398 tok | 不得记在 ICG/CR 头上 |
| 双 Token B/C：独立贡献**未证实** | **禁止**双 Token 主张 |
| 1.5B testpart：ICG 门 PASS；VSO 回归 PASS | 仅作本地筛选，**非**论文确认性 |
| V13B special(OSCA+倒排) ≡ testpart | **不进**本实验臂；不作 V13C |

**本实验主问题：**

1. **H-B1**：`vam_coder_v1.3B_ICG` 相对 `vam_coder_v1.2_F` 是否降低 Episode Total Prompt，且 ESR 非劣？  
2. **H-B2**：`vam_coder_v1.3B_ICG` 相对 `vam_coder_v1.3A_CR`（related 全跳过）是否在 prompt 不劣的前提下 ESR 不更差（或 prompt 更低且 ESR 非劣）？  
3. **机制**：ICG 的 `icg_full`/`icg_skip` 剂量是否 ≥ 预声明下限（防“算法没跑”）。

**明确不做：** ESR 优效主张；KV 显存；双 Token；OSCA/倒排增量；跨模型绝对 token 合并。

---

## 1. 臂定义（冻结）

| 臂 | 架构 ID | 机制 |
| --- | --- | --- |
| **A（对照）** | `vam_coder_v1.2_F` | V12-F：相关非目标 FULL + O′ |
| **B** | `vam_coder_v1.3A_CR` | V13A：C 库 + related 一律跳过（`cr_related_mode=compact`） |
| **C（主）** | `vam_coder_v1.3B_ICG` | V13B：继承 C 库 + **ICG** 选取 related FULL 子集 |

配置字段（`AblationConfig`）：

| 字段 | A=F | B=CR | C=ICG |
| --- | --- | --- | --- |
| `non_target_related` | full | full | full |
| `cr_enabled` | false | true | true |
| `cr_related_mode` | full | compact | full |
| `icg_enabled` | false | false | **true** |
| `icg_budget_tokens` | 512 | 512 | **512** |
| `osca_enabled` / `retrieval_enabled` | false | false | **false**（特别版不进本实验） |
| `o_prime` / E/C 禁 O′ / must 闭包 | 冻结默认 | 同 | 同 |

**VSO**：已离线回归 PASS（`vso_regression_v13b`，31 场景 + 双臂 0 mismatch）；本实验**不改** VSO 代码。

---

## 2. 任务集与规模（冻结）

### 2.1 主任务集（推荐）

| 项 | 值 |
| --- | --- |
| 任务集 | **`p1/tasks_independent_v1/`**（48 题，与 P1 泄漏审计已过） |
| 或备选 | 独立集 + 已冻结 holdout 合并（若剂量不足则**禁止**用 screen 题冒充确认性） |
| 步长分布 | short 2 / medium 5 / long 10（沿用） |
| 重复 | **R=3**（成本折中；若 S5 允许可升 R=5） |
| 规模（R=3） | 48×3 臂×3 = **432 episodes**；请求 ≈ 272×3×3 = **2436** |
| 随机化 seed | **20261112**（开跑前写入 run_meta；仅乱序） |
| Bootstrap | seed=**20261102**, B=10000, cluster=**task_id**（冻结） |

### 2.2 剂量门（D1 路径，2026-11-09 更新）

**执行结果 v1（independent 单独）**：cand 3.68% < 15% → FAIL → 启用 **D1**。

**D1 增补集** `p1/tasks_independent_v1_dose/`（8×5 步）：

- 判别性 0 问题；泄漏审计全过（禁词/包含/sha/集内唯一）  
- ICG 修正：正向「参考」子句命中增益 ≥1.5  

| 层 | cand 步比 | icg_full/候选 | 门（分层） |
| --- | ---: | ---: | --- |
| **dose 增补集** | **52.5%** | **100%** | **≥15% / ≥10% → PASS** |
| independent 原集 | 3.7% | 90% | 低剂量层，**披露** |
| 合并 | 9.9% | 96.8% | **不设总 15% 门**；主分析按 dose+/dose− 分层 |

**冻结版门（D1）：**

1. **主门**：dose 增补集单独 cand≥15% 且 full/候选≥10% 且 ET/must 违规=0 → 已 **PASS**（`dose_dryrun/dose_report_v2.json`）  
2. **分层**：确认性主表必须分层报告 **dose+（增补集）** vs **dose−（independent 原集）**  
3. **禁止**：以合并集 9.9% 冒充总 15% 门；禁止在剂量不足层单独下「ICG 无效」结论  

产物：`p1/experiments/v13b_deepseek/dose_dryrun/dose_report_v2.{json,md}`  
增补集：`p1/tasks_independent_v1_dose/`（leakage_audit.json）

### 2.3 若 independent 尚未跑完

`independent_validation` 审计时仅 24/720。本实验**依赖独立集文件冻结**（sha 已在 Part3）；运行完整性由 orchestrator 断点续跑保证。**不**与未完成的 V12-F 确认性混并统计（分表报告）。

---

## 3. 模型与配置（冻结）

| 项 | 值 |
| --- | --- |
| 模型 | `deepseek-v4.1-flash-1017` @ 既有 endpoint |
| 鉴权 | `VAM_API_KEY` 环境变量（不写产物） |
| 解码 | temperature=0, seed=0, **max_tokens=2048**, history=keep(24000) |
| 闭包/预算 | d=2, K_max=8, budget=4096, window=8192 |
| SYSTEM_PROMPT / build_messages / p1_common | 沿用冻结 sha（`4f591635…` / `f0b477b0…` / `b6ce07a3…`）**或** P3 后已钉新 sha——开跑前 `run_meta` 逐项核验，不一致即停 |
| runner | `run_p1_v12.py`（含 `V13ACR`/`V13BICG`/`MEMORYOFF` 臂） |
| code snapshot | 开跑前记录 `config.digest()` 三臂 + `icg.py`/`levels.py`/`assemble.py` 文件 sha |

---

## 4. 主假设与判定（冻结）

### 4.1 效率（RQ 对齐）

- **H-B1a**：task 级配对 `C − A` 的 prompt/episode 均值差 **< 0**，且 95% CI 不含 0（sign-flip + Holm 见下）。  
- **H-B1b**：`C − B` 的 prompt/episode 差 **≤ 0**（ICG 不得比全跳更贵超过 1%：允许 CI 上界 ≤ 0.01×|B|）。

### 4.2 能力（非劣，界值 **−12pp**，与 P1 相同）

- **H-B2a**：`C − A` 的 ESR 配对差 95% CI **下界 ≥ −12pp**。  
- **H-B2b**：`C − B` 的 ESR 配对差 95% CI **下界 ≥ −12pp**。

### 4.3 安全（硬门，非假设检验）

- 三臂 **INSUFFICIENT = 0**（或仅允许与 P1 同口径的 protocol 触顶并计入 ESR 失败）  
- **DHO = 0**；pre_send 违规后仍请求 = 0  
- VSO：沿用离线回归结论；若 run 中出现 architecture 类安全缺陷 → **S1 停机**

### 4.4 机制剂量（描述 + 门）

- 报告臂 C：`icg_full` / `icg_skip` / `extract force` 计数与占比  
- 门：见 §2.2 dry-run；正式 run 中若 `icg_full+icg_skip` 相关候选步 =0 → 标 **剂量失败**，H-B1 不得判支持

### 4.5 多重比较

预指定 **两条主比较**（效率与非劣各一次 Holm，α=0.05）：

1. **C − A**（ICG vs V12-F）  
2. **C − B**（ICG vs CR-skip）  

B − A 为次要。分层（难度/archetype）、Growth、Peak 为次要/描述。

### 4.6 Growth 口径

- 报告 OLS Growth，**标注 ESR 混杂**（成功多→历史长）  
- **不**以 Growth 单独作通过/失败门；Peak 与 prompt 为主

---

## 5. 运行与失败分类（沿用 P1）

- 断点续跑 + resume-cleanup（P2 已验证）  
- 错误分类：protocol / architecture / task / infrastructure；protocol **计 ESR 失败**  
- 排除：**无事后排除**；infra 整轮失效可重跑并记审计  
- S5：dry-run 估算 ×2 写入 run_meta（独立集 P1 实测约 2.80M×(3臂×R3/3臂×R5) 量级——以 dry 为准）  
- 就绪门：前 36 集若三臂 ESR 全 0/全 1 或 protocol>20% → 只停不调

---

## 6. 统计分析（沿用 + 本实验落点）

| 项 | 值 |
| --- | --- |
| 单位 | task_id |
| 主检验 | task 级配对 sign-flip（双侧） |
| 区间 | task-cluster bootstrap 95% CI（seed 20261102, B=10000） |
| Holm | 主比较 C−A、C−B（效率与 ESR 各族） |
| 非劣 | margin −12pp（下界） |
| NA | TPSE 零成功 → NA + na_ratio（沿用） |
| 分表 | 与历史 P1/P2/双Token **不合并**绝对值 |

---

## 7. 执行顺序（全部满足才允许正式请求）

1. ~~剂量路径选定~~ → **已选 D1 并 PASS**（§2.2，dose_report_v2）  
2. 本档 **用户确认 → 冻结 v1**，sha 写入 `p1/experiments/v13b_deepseek/prereg_freeze.json`  
3. 代码快照 + 三臂 `config.digest()` 入 run_meta（含 ICG ref-clause 修正）  
4. 剂量报告 v2 附录 + VSO 回归 PASS 附录  
5. 冒烟：每臂 2 集真模型（FILE 协议、usage 字段）  
6. 全量 orchestrator：任务 = independent 48 + dose 8 = **56**，seed=20261112，分层分析  
7. 分析脚本预写（bootstrap/Holm/非劣/dose 分层）后锁分析配置  

**当前状态：v1 已冻结（2026-11-09）→ 下一步为代码快照 + 冒烟（仍须按 §7 顺序）。**

---

## 8. 诚实条款（写入论文边界）

1. 1.5B testpart / 三臂 compare **仅筛选**，不进主表。  
2. OSCA/倒排 special **无增量**，不进臂、不进贡献。  
3. 双 Token **不进**贡献列表。  
4. ICG 若相对 A 的 prompt 降幅小，仍可主张「非劣 + 选择可解释」，但**不得**夸大为 O′ 级收益。  
5. 独立集与 P1 效应量**分表**，同模型才比方向。

---

## 9. 冻结核对清单（v1 已勾）

- [x] 臂 ID / config 字段表确认  
- [x] 任务集路径与 R、seed、S5（R=3 候选，S5=dry×2 开跑前写入）  
- [x] 主比较两条 + Holm 族定义  
- [x] 非劣界 −12pp  
- [x] 剂量门数值（D1 分层，dose 集 PASS）  
- [x] 不做清单（双Token/OSCA/KV/ESR优效）  
- [x] 代码快照清单（开跑前执行）  
- [x] 用户书面「冻结」（2026-11-09）  

---

## 10. 变更记录

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| v0.1 | 2026-11-09 | 草稿；D1 剂量门写入 |
| **v1** | **2026-11-09** | **用户确认冻结；D1 dose PASS 附录；未发任何确认性请求** |

（完）
