# VSO 安全省略边界与故障注入验证 — 实验设计文档

**VSO Safe-Omission Boundary and Fault-Injection Evaluation**  
状态：**v2 已冻结（用户授权继续推进；§11 歧义按文档默认值钉死：FBR=False Block Rate、FBR≤0.1、FSR≥0.9、C4 单实例、H2=FORCE_FULL、B2=历史发送事实口径）**  
日期：2026-11-06 · 排产优先级 #2（P3-A 跨模型实验之后的下一个重点）

**修订记录**：v2 按审阅意见完成 9 项修订（见 §10 修订对照表）。v1→v2 主要变化：三机制基线显式化与 V1–V5 三列预期、指标分子分母数学化并引入 `expected_decision`/`observed_decision`、H4 纳入负向统计并增加 `attempted_dho`/`final_dho`、正向样本枚举 ≥8 个互异条件（含动态更新）、Phase2 十场景 ID 冻结、0.8 降格为工程验收阈值并预冻结四指标联合判定、V4/V1/C1/C3/H1 增加端到端装配路径测试、基础矩阵规模与条件性扩展条款明确化、生产代码只读与暂停报告程序条款化。

---

## 1. 核心科学问题

> 当系统**无法证明**某项必要信息已经安全地交付给模型时，VSO 能否阻止该信息被省略，并触发**正确的回退或阻断**？

配套对照问题（创新性判据）：

> **VSO 相比 B1（普通内容 Hash Check）与 B2（Cache Consistency Check）究竟多提供了什么安全保证？**  
> 若 B1/B2 能拦截全部可见性故障，VSO 的独立价值需重新证明；若 VSO 能稳定识别 **V4（内容没有变化，但必要信息实际上没有出现在最终 messages）** 这一类只有"可见性证明"才能覆盖的问题，则构成机制差异的直接证据。

本实验**不**回答成功率/token 效率问题（P1/P2 已覆盖）；**不**重新解释任何冻结定义（见 §7）。

## 2. 术语与冻结引用（禁止本实验内重释）

### 2.1 三机制（作为省略授权判据的对照定义）

| 机制 | 代号 | 判定内容（授权省略的充要口径） | 不覆盖的问题 |
| --- | --- | --- | --- |
| **普通内容 Hash Check** | **B1** | 注入内容 sha256 与当前磁盘文件 sha256 一致（内容完整性、逐文件） | 不看历史、不看最终 messages；无法回答"内容是否曾/仍在交付面中" |
| **Cache Consistency Check** | **B2** | 同一 sha256 曾成功发送过（缓存命中 / REUSE 路径的"发过相同内容"判据） | 不回答"该发送是否仍存在于最终 messages"（历史被裁剪后 B2 仍可能成立） |
| **VSO（可见性证明）** | **VSO** | 同 sha256 内容**确实出现在最终 messages**（历史授权 + 发送前 `verify_omissions_in_messages` 终判） | 不覆盖 must/预算/目标约束（由 C 层与 r2.2 规则负责，协同判定） |

**公平性条款**：B1、B2 与 VSO 在同一场景上接收**完全相同的输入、故障与执行条件**；B1/B2 按各自机制的最强真实能力评估，不人为削弱。B1 的真实强项（装配内容被篡改类故障）不属于本可见性矩阵范围，如实声明而不构造充数。VSO 相对 B2 的预期增益集中在 V4 类（发送过 ≠ 仍在最终 messages），相对 B1 的增益覆盖全部"存在性/证明性"故障（V1–V5 中除 V4 外 B2 多数亦可拦，如实报告，不夸大）。

### 2.2 冻结术语（本实验内不得重释）

| 术语 | 冻结定义来源 |
| --- | --- |
| DHO | rev3 §3.3.1 / 代码口径：`plan.edit_targets ∩ post.omitted_files` |
| O′ / VSO 省略证明 | `v11.visibility.safe_omission` + `proof.tracker_from_history` + `messages_visibility.verify_omissions_in_messages` |
| must | `levels.dependency_closure` 的 must_full（E⊆M、r2.2）；强制保留不得被省略逻辑覆盖 |
| INSUFFICIENT | rev3 §4.6：请求前上下文/验证不足、未发模型请求（含 `MISSING_REQUIRED_FILE`、`REQUIRED_CONTEXT_EXCEEDS_LIMIT`、pre_send 失败） |

### 2.3 决策词汇（`expected_decision` / `observed_decision`，四值封闭）

| 值 | 含义 |
| --- | --- |
| `ALLOW_OMISSION` | 允许省略该信息并继续执行 |
| `FORCE_FULL` | 拒绝省略、改以全量交付后继续执行 |
| `INSUFFICIENT` | 判定无法完整交付，**不发模型请求** |
| `BLOCK` | 系统级硬阻断/异常停机路径（S1 类） |

- 每个样本在场景矩阵中**预置唯一** `expected_decision`；运行后记录唯一 `observed_decision`。
- 本矩阵**无样本**的 `expected_decision = BLOCK`；若负向样本上观察到 `BLOCK`，计入决策不匹配，但**不**计入 Unsafe Omission。

## 3. 场景矩阵（三层 + 正负样例 + 三机制对照）

### 3.1 Layer V — 可见性证明层（V1–V5）

列含义：三机制在该故障下的**授权判定**（授权省略 / 拒绝省略）；`expected_decision` 为 VSO 管线的期望。

| ID | 场景（初始状态 → 故障注入 → 可机检通过条件） | B1 预期 | B2 预期 | VSO 预期 | expected_decision |
| --- | --- | --- | --- | --- | --- |
| **V1** | tracker 持有旧版本 sha，磁盘文件已变更；通过条件：该文件不被省略且出现在最终 messages | 授权省略（磁盘自洽） | 拒绝省略（新 sha 未发送过） | **拒绝省略**（证明过期） | `FORCE_FULL` |
| **V2** | 目标文件无任何可见性记录；通过条件：不被省略 | 授权省略 | 拒绝省略（从未发送） | **拒绝省略** | `FORCE_FULL` |
| **V3** | 证明条目 sha ≠ 当前文件 sha（记录被篡改/漂移）；通过条件：不被省略 | 授权省略（注入内容仍=磁盘） | 拒绝省略（该 sha 无发送记录） | **拒绝省略**（证明与实际不一致） | `FORCE_FULL` |
| **V4（核心区分）** | 同 sha 内容曾发送，但对应 assistant 消息**不在最终 messages**（历史裁剪/重排）；通过条件：不被省略，且信息以全量形式出现在最终 messages | 授权省略 | **授权省略**（曾发送成功） | **拒绝省略**（可见性不成立） | `FORCE_FULL` |
| **V5** | 多步链中外部修改覆盖文件，tracker 仍持旧证明；通过条件：按当前 sha 重新验证失败 → 不省略 | 授权省略 | 拒绝省略 | **拒绝省略** | `FORCE_FULL` |

**V4 是核心区分场景**：唯一预期出现"VSO 拒绝而 B1、B2 均授权"的样本（VSO 独占检出的定义样本，见 §5）。若 VSO 在 V4 上不能稳定识别，其独立创新价值按 §5 联合判定不得通过并须在报告中如实重审。

### 3.2 Layer C — 约束与预算层（C1–C4）

| ID | 场景与可机检通过条件 | expected_decision | 附加断言 |
| --- | --- | --- | --- |
| **C1** | 构造 must 文件进入省略候选；通过条件：must 仍全量交付 | `FORCE_FULL` | E⊆M 不变量；must 文件出现在最终 messages |
| **C2** | edit target 同时被标为可省略（target/记忆检索/省略策略三方冲突）；通过条件：r2.2 优先，target 强制 Full | `FORCE_FULL` | target ∈ 最终 messages；DHO=0 |
| **C3** | required_context_tokens > context_window；通过条件：按 INSUFFICIENT 路径**不发请求**（预算耗尽 ≠ 可安全省略） | `INSUFFICIENT` | 该步 requests=0；insufficient_reason 记录 |
| **C4** | 装配预算仅超可选项、must 可容纳；通过条件：仅可选 digest/optional 按既有规则被丢弃，must 全在 | `ALLOW_OMISSION`（仅限可选内容） | must 全量出现；`over_budget` 审计标记存在 |

### 3.3 Layer H — 历史与信息完整性层（H1–H5）

| ID | 场景与可机检通过条件 | 分级 | expected_decision |
| --- | --- | --- | --- |
| **H1** | 单条 assistant 消息损坏（内容 hash 失败、结构完整）；通过条件：该条**不得**授权省略，回退全量，不静默使用损坏历史 | 可恢复 | `FORCE_FULL` |
| **H2** | history 截断至仅 system / 角色错乱（不可恢复）；通过条件：无任何省略授权发生，回退全量 | 不可恢复 | `FORCE_FULL` |
| **H3** | must 文件从磁盘缺失；通过条件：`MISSING_REQUIRED_FILE` → 不发请求 | — | `INSUFFICIENT` |
| **H4** | 构造 `omitted ∩ edit_targets` 非空的企图；通过条件：装配/发送前拦截，`attempted_dho > 0` 且 `final_dho = 0` | — | `FORCE_FULL` |
| **H5** | 动态信息项：更新后的文件**未**重新证明仍被尝试省略；通过条件：拒绝省略、更新内容重新交付 | 动态 | `FORCE_FULL` |

**H4 计量（纳入负向统计）**：H4 属负向样本（进入 UOR 分母）。逐步记录两个字段：
- `attempted_dho` = 故意构造后、防护生效前的 `|edit_targets ∩ omitted|` 企图值；
- `final_dho` = 按**冻结公式**（§2.2）在最终状态计算的值，通过条件 `final_dho = 0`。
全局汇总报告 `Σ attempted_dho` 与 `Σ final_dho`（后者必须为 0）。

### 3.4 正向样本与样本构成（防"全不省略"刷分）

**正向安全省略样本（≥8 个互异条件，禁止同条件改参数凑数）：**

| ID | 条件（互异维度） | expected_decision |
| --- | --- | --- |
| **P1** | 近期可见：上一步 assistant FILE 回写、文件未变 | `ALLOW_OMISSION` |
| **P2** | 跨步可见：证明来自 k−2 步、中间无修改 | `ALLOW_OMISSION` |
| **P3** | 多文件批：≥3 个文件**各自独立证明**后同时省略 | `ALLOW_OMISSION` |
| **P4** | 混合批：1 个省略 + 1 个全量 target 共存于同一步 | `ALLOW_OMISSION` |
| **P5（动态信息·正向）** | 文件在本步更新 → **新 sha 重新证明**后省略（更新后重新验证与交付） | `ALLOW_OMISSION` |
| **P6** | 模型输出回写：文件内容 = 最新 assistant FILE 块，hash 匹配 | `ALLOW_OMISSION` |
| **P7** | O′/REUSE 正常路径：缓存命中且最终 messages 含同内容 | `ALLOW_OMISSION` |
| **P8** | 长历史：证明位于 trim 预算内仍可见 | `ALLOW_OMISSION` |
| **P9** | must 邻接非 must 文件：相关但非 must、已证明 | `ALLOW_OMISSION` |

**负向样本**：V1、V2、V3、V4、V5、C1、C2、C3、H1、H2、H3、H4、H5 = **13 个**（H4 已纳入，见 §3.3）。  
**假阻断对照**：正向 9 条在无故障重复执行下的对照运行（≥8 个独立执行实例）→ FBR 分母。  
**样本总量**：13 负向 + 9 正向 + 8 假阻断对照 ≈ **30（基础矩阵约 29–30，维持规模）**；B1/B2 基线对 13 个负向逐场景运行。

**基础矩阵与条件性扩展条款**：并发场景、多文件批量交叉污染场景**不主动纳入**。仅当实现前的代码路径审计证明 harness 存在真实并发执行路径、或存在多文件证明交叉污染路径时，才以修订案形式提请增补；无该路径则不人为构造。基础矩阵规模维持 ≈29，不扩张。

**防刷分与联合判定（预冻结）**：
- `SOR ≥ 0.8` 仅为**工程验收阈值**，预先冻结、不得事后调整；达到阈值**不得**解释为"VSO 已具备充分安全性"。
- **四指标联合判定（预先冻结）**：本实验"通过" ⇔ 同时满足  
  **UOR = 0 ∧ SOR ≥ 0.8 ∧ FBR ≤ 0.1 ∧ FSR ≥ 0.9**。  
  四指标必须同表联合呈现（安全象限 × 可用象限），任一不满足即判不通过并在报告中给出失败象限。
- 系统不得通过"完全禁止省略"得分：该行为会使 SOR 低、FBR 高（见 §5 数学关系），自动落入不通过象限。

## 4. 两阶段执行

### Phase 1 — Harness 级（无模型，确定性）

- 对象：`visibility` / `proof` / `levels(must)` / `assemble` / `pre_send verify` / INSUFFICIENT 门闩 / DHO 后检 的**函数级故障注入**（仅测试进程内构造输入或 monkeypatch，**不修改任何生产路径代码**）。
- 每样本断言：① `observed_decision`（四值之一）② 最终 messages 中的信息点存在性 ③ `attempted_dho`/`final_dho`（H4）④ 该步请求数（INSUFFICIENT 时=0）⑤ 与 `expected_decision` 的逐样本比对。
- B1/B2 基线在**同输入、同故障、同执行条件**下对 13 个负向场景各跑一遍（授权判据替换，其余不变）。

**端到端装配路径子集（v2 新增）**：**V4、V1、C1、C3、H1** 五个场景除函数级注入外，必须额外执行**完整装配路径**：`plan → assemble → build_messages → verify_omissions_in_messages →（期望路径下的）请求门闩`，并在**实际产出的最终 messages**（`messages.json` 全文）上做信息点存在性机器检查——证明层断言与真实交付面一致，而非只在中间结构上成立。

### Phase 2 — 真模型确认性子集（DeepSeek 主模型）

| 阶段 | 模型 | 目的 |
| --- | --- | --- |
| Phase1 | 无模型 harness | 确定性安全逻辑 |
| **Phase2** | **DeepSeek 主模型（deepseek-v4.1-flash-1017，与 P1/P2 同源）** | 真实模型调用链路中的机制确认 |
| 后续扩展（本轮不做） | Qwen | VSO 跨模型稳健性 |

- **Phase2 场景 ID（预冻结，禁止事后挑选）**：**`V1, V4, C1, C2, C3, H1, H2, V5, P1, P5`**（负向8：V4、must 冲突 C1/C2、预算耗尽 C3、history 损坏 H1/H2、动态更新负向 V5、证明过期 V1；正向2：近期可见 P1、动态重验证省略 P5）。
- 规模：**10 场景 × R3 = 30 集**；参数与 P1 冻结一致（max_tokens=2048、temp0、seed0、keep）。
- **定位：真实执行链路的确认性测试**——不单独承担显著性检验、不外推广泛泛化结论；报告以逐场景断言结果为主。
- P3-A（qwen 跨模型）与本实验互不混同。

## 5. 指标定义（分子/分母/数学关系，全部预冻结）

设样本全集 $S$，按预置期望划分：
- 负向集 $S^- = \{s \in S : expected(s) \neq \texttt{ALLOW\_OMISSION}\}$（13 场景对应样本）；
- 正向集 $S^+ = \{s \in S : expected(s) = \texttt{ALLOW\_OMISSION}\}$（P1–P9）；
- 回退期望集 $S^{fb} = \{s \in S^- : expected(s) \in \{\texttt{FORCE\_FULL}, \texttt{INSUFFICIENT}, \texttt{BLOCK}\}\}$（当前矩阵 $S^{fb} = S^-$）。

| 指标 | 分子 | 分母 | 关系与目标 |
| --- | --- | --- | --- |
| **UOR（Unsafe Omission Rate）** | $\|\{s \in S^-: observed(s)=\texttt{ALLOW\_OMISSION}\}\|$ | $\|S^-\|$ | **目标 = 0**（硬安全项） |
| **SOR（Safe Omission Rate）** | $\|\{s \in S^+: observed(s)=\texttt{ALLOW\_OMISSION}\}\|$ | $\|S^+\|$ | 验收 ≥ **0.8**（工程阈值） |
| **FBR（False Block Rate）** | $\|\{s \in S^+: observed(s)\neq\texttt{ALLOW\_OMISSION}\}\|$ | $\|S^+\|$ | **SOR + FBR ≡ 1**（正向集二分，恒等式）；验收 ≤ **0.1** |
| **FSR（Fallback Success Rate）** | $\|\{s \in S^{fb}: observed(s)\neq\texttt{ALLOW\_OMISSION} \wedge \text{交付不变量成立}\}\|$ | $\|S^{fb}\|$ | 交付不变量 = 信息在最终 messages，或 INSUFFICIENT 时 requests=0；验收 ≥ **0.9** |
| **EDR（Evidence/Visibility Detection Rate）** | 各机制在 $S^{vis}=\{V1..V5\}$ 上判"拒绝省略"的样本数 | $\|S^{vis}\|$ | 报告 `EDR_VSO / EDR_B1 / EDR_B2` 三列并排 |
| **VSO 独占检出数** | $\|\{s \in S^{vis}: VSO拒 \wedge B1授 \wedge B2授\}\|$ | —（计数） | 核心创新证据；设计预期 ≥1（V4） |
| **Decision Accuracy** | $\|\{s \in S: expected(s)=observed(s)\}\|$ | $\|S\|$ | 总体决策正确率（与上表联合呈现） |

补充恒等/边界：
- 正向集上 `SOR + FBR = 1`；若观测只有四值，则 $S^+$ 上 observed 非 ALLOW 即计入 FBR（无论表现为 FORCE_FULL/INSUFFICIENT/BLOCK）。
- `UOR = 0` 与 `FSR ≥ 0.9` 同时报告：出现 `observed ≠ ALLOW` 但交付不变量破坏的情形计入 FSR 分子之外，故 **UOR + FSR ≤ 1** 的缺口必须单列说明。
- **四指标联合判定**（§3.4 预冻结）：通过 ⇔ UOR=0 ∧ SOR≥0.8 ∧ FBR≤0.1 ∧ FSR≥0.9；0.8 仅为工程验收阈值。
- H4 汇总：`Σ attempted_dho`（>0 证明故障注入生效）与 `Σ final_dho`（=0 为通过条件）。

**（缩写说明见 §11 歧义表：FBR 取 False Block Rate。）**

## 6. 实现清单与测试隔离（生产代码只读）

| 注入点（全部限定测试侧） | 对应场景 |
| --- | --- |
| `VisibilityTracker.mark_from_assistant` / tracker 内容 | V1, V2, V4, V5, H1, H2, P1–P8 |
| `safe_omission(desired_sha, …)` 入参 | V3, V5, P5 |
| `build_plan` 的 must 集合与省略候选 | C1, C2, C4, P4, P9 |
| `required_context_tokens_est` / 装配预算判定 | C3, C4 |
| 磁盘文件缺失 | H3 |
| `verify_omissions_in_messages` 输入 messages | V4, H1, H2 |
| DHO 后检（**冻结公式**，只读计算） | H4 |
| 动态更新注入（步间改文件 + 重证明时点控制） | H5, P5 |
| 基线判据实现（B1：sha(注入) vs sha(磁盘)；B2：sha 曾发送记录） | 13 个负向场景对照 |

**测试隔离铁律（v2 条款化）**：
1. `p1/scripts` 与 `src/` 生产代码**只读**——本实验不修改、不加开关、不重构；
2. 所有故障通过测试进程内的输入构造、临时对象注入或 monkeypatch 施加；
3. **若实现中发现必须修改生产代码才能注入某场景 → 立即暂停，输出报告说明修改点与必要性，等待批准；禁止顺手修改**；
4. 不得修改 P1/P2 已冻结的数据与口径；不得运行本实验以外的实验；不得 Git 写操作。

## 7. 明确不做（边界）

1. 不重释 DHO、INSUFFICIENT、must、O′（§2.2 表）。
2. 不用本实验结果修改 P1/P2 冻结口径（协议违规复测、消融结论各归各）。
3. 不含记忆污染/错误传播（P3-B/MEPR 另案）。
4. 不做架构间 ESR/token 比较。
5. 不主动扩展并发/多文件新层次（§3.4 条件性条款）。
6. 基线不许事后替换或削弱：B1、B2 定义与 §2.1 写死。

## 8. 交付物

**本阶段（修订）唯一交付物**：修订后的本文档。  
后续阶段（须经审阅并收到最终冻结指令后才启动）：`scenario_matrix.csv`（六要素逐样本 + `expected_decision` + B1/B2 预期列）→ `vso_harness.py`（Phase1 含五场景端到端子集）→ Phase1 运行 → Phase2（`run_meta` 冻结同 P1 规格）→ `vso_results.csv` + `vso_report.md`（含三机制检出对照、四指标联合判定、V4 独占检出专节）。

## 9. 排期（含冻结前检查点）

1. **设计审阅（当前）** → 用户逐条审查 §3 场景定义、§5 指标分母与联合判定、§6 测试隔离、§9 执行顺序；
2. **审查通过 + 最终冻结指令** → 冻结文档 SHA 并记录；
3. 写 `scenario_matrix.csv`（六要素 + expected/基线预期全列）；
4. 实现 Phase1（含 §4 端到端子集）→ 运行 Phase1；
5. Phase2（DeepSeek，10 场景×R3）；
6. 报告与联合判定。  
**冻结前检查点清单（逐项确认后方冻结）**：基线公平性（B1/B2 同输入同故障）· VSO 独占检出定义（V4）· 假阻断与真实安全阻断的区分（FBR vs UOR）· 正向省略防刷（SOR/FBR 恒等 + 联合判定）· 动态信息更新后重新验证与交付（P5/H5）· 失败处理具体行为（FORCE_FULL/INSUFFICIENT/BLOCK 四值闭合）· 生产代码只读与暂停报告程序（§6）。

## 10. 修订对照表（v1 → v2，对应审阅任务9项）

| # | 要求 | 修订位置 |
| --- | --- | --- |
| 1 | B1/B2/VSO 三机制显式区分，V1–V5 三列预期，基线不削弱，V4 保留 | §1、§2.1（含公平性条款）、§3.1 三列预期表 |
| 2 | SOR/FBR/UOR 分子分母与数学关系 + `expected_decision` 四值 | §2.3、§3 全表 expected 列、§5 公式与恒等式 |
| 3 | H4 纳入负向 + `attempted_dho`/`final_dho` | §3.3 H4 行、§3.4 负向清单、§5 H4 汇总行 |
| 4 | 正向 ≥8 互异条件含动态更新 | §3.4 P1–P9 表（P5=动态重验证正向） |
| 5 | Phase2 十场景 ID 冻结 | §4 Phase2（`V1,V4,C1,C2,C3,H1,H2,V5,P1,P5`） |
| 6 | 0.8=工程验收阈值 + 四指标联合判定预冻结 | §3.4 末、§5、§9 检查点 |
| 7 | V4/V1/C1/C3/H1 端到端装配路径 + 最终 messages 检查 | §4 Phase1「端到端装配路径子集」 |
| 8 | ≈29 基础场景，不主动扩展（条件性条款） | §3.4 构成与扩展条款、§7.5 |
| 9 | 测试侧注入、生产代码只读、必要修改时暂停报告 | §6 铁律四条、§7.6 |

## 11. 剩余歧义（请审阅时裁定）

1. **FBR 缩写**：本稿取 **False Block Rate**（与 SOR/UOR 同族的错误率指标）；若原意为 Fallback Success Rate，本稿已另设 FSR——请确认取舍或两者并存（现为并存：FBR+FSR 同时报告）。
2. **联合判定阈值数值**：UOR=0（硬项）之外，SOR≥0.8 沿用约定；**FBR≤0.1、FSR≥0.9 为本稿拟定值**，是否认可请裁定。
3. **C4 的 expected 判定**：本稿将 C4 拆为"仅可选超预算、must 可容纳"的单一实例（expected=`ALLOW_OMISSION` 限可选内容）；若要求覆盖"must 也放不下 → INSUFFICIENT"的第二分支，需作为 C4b 增加样本（会把基础矩阵 +1）。
4. **H2 的 expected 判定**：本稿定为 `FORCE_FULL`（无证明 → 全量回退、不静默）；若贵方预期 H2 走 `INSUFFICIENT` 路径，请指出——这取决于 harness 对"不可恢复历史"的实际处理，Phase1 实现前应按真实代码路径确认。
5. **B2 的判定时点**：B2 = "该 sha 曾成功发送过"（历史事实），因此 V4 中 B2 授权是其机制的真实结论；若 B2 另有"以最终 messages 为界"的口径，则 B2 与 VSO 定义重叠——请确认采用"历史发送事实"口径。

**冻结记录**：v2 冻结于 2026-11-07（用户指令「继续推进VSO专项实验」视为审阅通过与冻结授权）；sha256 见 `p1/experiments/vso_fault_injection/design_freeze.json`。冻结后任何修改 = 版本+1 + 变更记录。
