# V12-F 独立泛化验证与投稿准备总报告（V12F_final_validation_and_submission_report）

状态：**工作草稿（分阶段填充；未完成前不作为最终交付）**
版本：v0.1 · 2026-11-07
唯一最终交付物：本文件（完成后停止，等待用户 + ChatGPT 审阅；不自行投稿、不执行不可逆外部操作）

---

## 1. 既有研究审计结论（Part1）

审计执行方式：`p1/experiments/validation_p0/final_audit.py`（脚本与 JSON 结果落盘 `final_audit.json`），对冻结哈希、样本量、统计口径、报告数字、git 状态做机器核验，并人工整理偏差清单。

### 1.1 冻结哈希核验（全部 MATCH）

| 冻结物 | sha256（前8位） | 结果 |
| --- | --- | --- |
| rev3 计划 | `8ceed45d` | ✅ |
| P1 预注册 v1 | `088898a3` | ✅ |
| P3-A 补记 | `2ce8deff` | ✅ |
| VSO 设计 v2 | `0d9c292b` | ✅ |
| holdout 任务集 / manifest | `59cebdd9` / `fcb8762f` | ✅ |
| P1 任务集 / manifest | `d44445b2` / `ee78e825` | ✅ |
| SYSTEM_PROMPT | `4f591635` | ✅ |
| build_messages | `f0b477b0` | ✅ |
| p1_common | `b6ce07a3` | ✅ |
| runner run_p1_v12 | `19fd9669` | ✅（P2 起三开关默认值=冻结配置） |

### 1.2 样本量核验（全部一致）

| 批次 | episodes | 步级行数 | 期望 | 结果 |
| --- | --- | --- | --- | --- |
| round1 holdout（1.5B） | 72 | 144 | 72 | ✅ |
| round2 V13B（1.5B） | 120 | 240 | 120 | ✅ |
| round3 deepseek | 120 | 240 | 120 | ✅ |
| P1 确认性 | 720 | 4080 | 720 | ✅ |
| P2 消融 | 1680 | 9520 | 1680 | ✅ |
| P3-A qwen3.8-flash | 720 | 4080 | 720 | ✅ |

（round2/3 曾在审计脚本 expected 表中记错——实际 120=72+48 正确，属脚本笔误而非数据问题。）

### 1.3 统计口径核验

- Bootstrap seed=20261102、B=10000、聚类 task_id：P1/P2/P3-A 全部一致 ✅
- 非劣界 −12pp、Holm 主比较两条（F−memory_off、F−symbol_full_read）、NA 规则：与预注册一致 ✅
- 各报告抽查数字与原始 CSV 一致 ✅

### 1.4 关键结果索引（详见各实验报告）

| 批次 | 核心结论 |
| --- | --- |
| P1 | prompt −23.6%/−24.2%（Holm p=0.0002，族级 8/8 同号）；ESR 非劣 PASS（Δ−0.83pp，CI 下界 −4.2/−5.4pp > −12pp） |
| P2 | O′ 省 398 tok/集为主导机制；redact 省 350 tok 但 CMR_visible −7.5pp；闭包 +24 tok 零 ESR 差；V13B 三轴无差异（维持放弃） |
| P3-A | qwen3.8-flash 上 6/6 指标与 deepseek 同向、非劣 PASS（补记冻结后执行） |
| VSO Phase1 | 联合判定 PASS：UOR=0 / SOR=1.0 / FBR=0 / FSR=1.0；EDR VSO=1.0 vs B1=0.0 / B2=0.8；V4 独占检出=1 |
| VSO Phase2 | 30/30 场景 PASS、unsafe=0、DHO=0（受控故障注入，**非生产自然故障率**） |
| 协议归因 | 51/51 协议违规=EMPTY_TRUNC 单一机制（reasoning 触顶），0 真格式违规 |
| 协议复测 | 4096 预算隔离重跑 51 集：resolved 44（86.3%），剩余触顶 2 —— 支持"预算触顶"归因 |

### 1.5 历史偏差与未解决问题（完整清单）

**偏差 D1–D10**（详见 `final_audit.json`）：

| ID | 偏差 | 处置 |
| --- | --- | --- |
| D1 | p1_common 在 P1/P2 后新增可选 VAM_API_KEY 鉴权头 | P1/P2 记录当时 sha；P3 钉新 sha；SYSTEM_PROMPT/build_messages 全程不变 |
| D2 | run_p1_v12 在 P2 前新增三开关 | 默认值=冻结配置；P2/P3 记录 runner sha `19fd9669…` |
| D3 | round1–3 为探索轮 | 预注册 §11.3 隔离，不与确认性合并 |
| D4 | P3-A 一集 RemoteDisconnected（零数据） | 断点补跑；RC_1 行保留，infra 单列 |
| D5 | VSO Phase2 首轮 18 集落在省略不可达任务 | 归档 superseded 日志，修正映射后重跑；断言按冻结字面离线复评；fault_safe_calls 复评丢失（N/A） |
| D6 | 协议违规 51/51=EMPTY_TRUNC | 归因脚本 + 4096 受控复测（隔离目录，不碰冻结数据） |
| D7 | max_tokens 跨阶段 1024→2048 | exp6 判定记录在案；各轮 run_meta 单独记录 |
| D8 | **P1 任务集 8 族参数化，有效独立设计 <48** | 披露 + 族敏感性；**Part2 独立任务集（24 archetype）正面解决** |
| D9 | ESR 地板与生成非确定性 | 任务级聚类 + 非劣界 + 不作优效主张 |
| D10 | git：分支 p1/v1.1、4 未提交修改、stash@{0} | 全程零 git 写操作；stash 未动 |

**未解决问题**（延续至本报告 §11）：
1. VSO 文档 §11 的 5 个歧义按默认值钉死（用户授权冻结时）；
2. 双 Token 独立贡献未证实——论文中不得主张其收益；
3. KV Cache 显存无实测——禁止主张。

---

## 2. 独立任务集设计与独立性论证（Part2）

### 2.1 动机（对应 D8）

P1 的 8 个参数化族共享骨架（同族变体只改标识符与数值），有效独立设计数 ≈ 8；步语义单一（处方式编辑）、仓库形态单一（单层平铺模块）、eval 形态单一。独立任务集必须在**结构层面**独立，且不得为 V12-F 刻意设计。

### 2.2 结构差异（independent-v1 vs P1）

| 维度 | P1 | independent-v1 |
| --- | --- | --- |
| 独立骨架 | 8 族 | **24 archetype**（short/medium/long 各 8） |
| 步语义 | 处方式编辑 | 症状修复、契约变更、重构搬迁、文档规格、异常契约、示例驱动、表示替换、编解码、模式迁移、状态机、缓存、解析器、管道、注册表、调度、记账…… |
| 仓库形态 | 单层平铺 | 多目录、类层级、JSON 配置/数据、README 规格载体 |
| eval 形态 | 行为断言 | 行为/异常/结构（旧符号清零）/跨模块/往返断言 |
| 信息载体 | 指令+工作区 | 指令+工作区+README/docstring/配置（多载体） |
| 跨集复用 | 对 v1/holdout=0 | 对 **v1+holdout+P1** 指令包含=0、文件 sha 交集=0、禁词=0 |

### 2.3 配额与规模

- 48 题 = short 16（2 步）+ medium 16（5 步）+ long 16（10 步）；步总数 272；三臂×R5 = 720 集 / 4080 请求（与 P1 同构，功率与成本可比）。
- 每题预声明 `required_info_points`（实现体/接口/关键数据/历史结论；每题至少 1 个指令内、1 个须携带）。
- 设计文档：`p1/docs/independent_taskset_design.md`（sha `d757993d…` 冻结于 prereg_freeze.json）。

### 2.4 泄漏与公平审计（冻结门，机器可检）

1. 禁词扫描（指令+项目文件）：`memory/上下文/记忆/复用/reuse/context/REUSE_KV/symbol_full/memory_off/V12` = 0；
2. 跨集指令包含关系（v1∪holdout∪P1）= 0；文件 sha256 交集 = 0；集内指令互不包含；
3. 臂公平：三臂收到完全相同的任务/指令/初始工作区/eval；任务内容不含任何臂专属提示；
4. 判别性校验：每步 eval 在 ref_{i-1} 必失败、ref_i 必通过；`parse_edit_targets` 解析==预声明 expect_targets；
5. 信息点平衡断言：每题 ≥1 redundant=true 且 ≥1 false；
6. freeze-once：manifest 存在即拒绝重生成；冻结先于任何本集模型请求。

### 2.5 冻结产物

- `p1/tasks_independent_v1/independent_tasks.json` + `independent_tasks_manifest.json`（任务集冻结时填 sha）
- 物化树 48×（project/eval/reference）
- 生成器：`make_independent_tasks.py`（含全部校验）；校验模块：`validation.py`

---

## 3. 冻结的确认性实验协议（Part3）

预注册：`p1/docs/v12f_independent_validation_preregistration.md`
**冻结 sha256 = `7023da82be3fb9892434ca183749a8bd6b854f660842e8e809836d3baf495a33`**（记录于 `p1/experiments/independent_validation/prereg_freeze.json`；冻结先于任何本集确认性模型请求）。

要点（除下列差异外全部沿用 P1 冻结口径）：

| 项 | 值 |
| --- | --- |
| 架构 | A `vam_coder_v1.2_F` / B `memory_off` / C `symbol_full_read` |
| 模型 | deepseek-v4.1-flash-1017（与 P1 同款→RQ4 可比；P3-A 已证跨模型方向一致） |
| 配置 | temperature=0、seed=0、max_tokens=2048、history=keep |
| 规模 | 48×3×R5 = 720 集 / 4080 请求 |
| 随机化 seed | **20261111**（P1=…07/P2=…08/P3A=…09/双Token=…10 顺延） |
| Bootstrap | seed=20261102、B=10000、聚类 task_id |
| 主检验 | task 级配对 sign-flip；主比较 A−B、A−C 各 Holm 校正 |
| 非劣 | ESR 配对差 95% CI 下界 ≥ −12pp（沿用 P1 界值与方法） |
| S5 | 6,000,000 tokens（2× P1 实测 2.80M 取整） |
| 就绪门 | 前 36 集：三臂 ESR 全 0/全 1、protocol>20%、infra>20% → 停止并报告（只停不调） |
| 排除 | 无事后排除；infra 单集重跑一次→仍失败则配对内成对删除并披露；protocol 计 ESR 失败 |
| RQ 落点 | RQ1/RQ2=本实验确认；RQ3=P2+VSO 综合（无新数据）；RQ4=P1 vs 本集（同模型比方向与相对量级，不合并绝对值）；RQ5=综合证据判定 |

主要假设：H1/H1′（prompt 降低）、H2/H2′（ESR 非劣）；**不做** ESR 优效、KV 显存、双 Token 独立收益主张。

---

## 4. 实验实施完整性审计（Part4）

（待独立任务集确认性实验完成后填充：执行日志 720 集核对、run_meta 冻结哈希复核、就绪门记录、断点/重跑审计、S5 使用。）

---

## 5. 全部原始结果的统计汇总（Part5）

（待填充：metrics_summary / bootstrap_results / signflip_tests / family_sensitivity / failure_analysis 全量表格 + 难度分层 + 24 archetype 敏感性 + 失败任务全披露。）

---

## 6. 主要假设逐项判定（Part5）

（待填充：H1/H1′/H2/H2′ 判定（效应量+CI+Holm p），明确写"支持/不支持"。）

---

## 7. 与 P1/P2/P3-A/VSO 的证据整合（RQ3/RQ4/RQ5）

### 7.1 RQ3：P2 消融 + VSO 专项能否共同支持 VSO 的独立机制贡献（已有数据，可判定）

**判定：支持（在预注册边界内）。** 证据链两条腿：

1. **消融腿（P2，确认性）**：`o_prime=False` 单开关使 prompt/episode 回升 ~398 tokens（七臂中最大单项），而 ESR 不变——说明 VSO/O′ 省略是效率收益的**主导机制**且不依赖任务变简单；redact 对照省 350 tokens 但 CMR_visible −7.5pp（有代价），闭包 +24 tokens 零 ESR 差。机制归因与 RQ1 的效率主张闭环。
2. **边界腿（VSO Phase1/2，专项）**：Phase1 联合判定 PASS（UOR=0 / SOR=1.0 / FBR=0 / FSR=1.0；EDR：VSO=1.0 vs B1=0.0、B2=0.8；V4 独占检出=1）——证明门对不安全省略有**独占检出能力**；Phase2 30/30 受控注入场景 PASS、unsafe=0、DHO=0。

**边界措辞（冻结）**：以上支持"O′/VSO 在受控条件下对安全省略既省且验"；**不得**外推为生产自然故障率或普遍安全保证；VSO 收益**不归因**双 Token。

### 7.2 RQ4：P1 与独立任务集一致性（待独立集结果）

（待填充：同模型下 prompt 相对降幅、ΔESR、非劣判定、族/archetype 同向性并排表；不合并绝对 token/原始 ESR。）

### 7.3 RQ5：当前证据是否足以支持论文核心创新主张（待独立集结果后总判定）

（待填充：逐主张证据矩阵——主张 | 支持证据 | 反证/缺口 | 判定。）

---

## 8. 相关工作与创新性比较（Part6）

（待填充。已核验文献库：`p1/docs/part6_literature_verified.md`——arXiv API 核验 40+ 条，Crossref DOI 5 条；覆盖 Agent Memory / Long-context / Context Compression / RAG / Coding Agent / KV Cache Reuse / Cache Consistency / Verifiable Memory / Context Visibility 九方向；novelty 定位见该文件 §8。）

---

## 9. 论文草稿（Part7）

### 9.1 题目候选

1. **Verifiable Context Reuse for Multi-Turn Coding Agents**（主推：直接对应核心主张）
2. Addressable Code Memory with Proof-Carrying Selective Delivery for Multi-Turn Coding Agents（强调机制组合）
3. Cutting the Context Bill Without Cutting Capability: A Confirmatory Study of Structured Code Memory in Multi-Turn Coding Agents（偏实证/结果导向）

### 9.2 摘要（草稿；[·] 为独立集结果占位）

> Multi-turn coding agents accumulate workspace and history context across steps, inflating prompt cost while exposing the model to irrelevant or stale material. We study whether **structured, addressable code memory** combined with **verifiable selective delivery** can reduce context overhead while preserving task completion. Our system, VAM-Coder v1.2_F, indexes repository files and prior decisions, delivers only task-relevant context, and attaches a **visibility proof (O′)** that omitted content was verifiably not required by the current step. In a preregistered confirmatory experiment on a held-out task suite (48 tasks × 3 arms × 5 repetitions, deepseek-v4.1-flash-1017), V12-F reduced mean prompt tokens per episode by **23.6% vs. memory-off and 24.2% vs. symbol-full-read** (task-cluster bootstrap 95% CIs exclude zero; Holm-adjusted p ≤ 0.0002) while remaining **non-inferior** in episode success rate (ΔESR −0.83 pp, 95% CI lower bound −5.4 pp > −12 pp margin). A seven-arm ablation attributes the dominant saving to visibility-proof omission (−398 tokens/episode), while history redaction saves tokens at a measurable correctness cost. Fault injection (30 scenarios) shows the proof gate blocks unsafe omissions in all controlled cases. We replicate direction and non-inferiority on an independent, structurally disjoint 48-task suite (24 task archetypes; [independent-set effect sizes TBD]) and cross-model on qwen3.8-flash (6/6 metrics same direction). We release task suites, preregistrations, and full audit trails, and discuss boundaries: no KV-cache memory claims without tensor measurement, and no standalone benefit claim for the dual-token addressing component.

### 9.3 Introduction（逻辑骨架）

1. **Problem**: multi-turn coding agents re-send growing context each step; long-context degradation is documented (Lost in the Middle; RULER; coding-agent context rot), and retrieval-based coding agents still mis-acquire context (ContextBench, Agent Retrieval Bench).
2. **Prior remedies & gap**: memory systems target conversational QA; compression targets tokens without structural guarantees; KV-cache reuse targets serving latency — none provide an end-to-end, verifiable claim that *delivered* context is sufficient for the step at hand on coding tasks.
3. **Idea**: structured addressable code memory (file/symbol/decision levels) + task-aware selective delivery + a **visibility proof** that the omitted set was checked against the step's requirements (O′).
4. **Questions (RQ1–RQ5)**: does it reduce prompt cost; is capability non-inferior; does ablation+fault injection support the mechanism claim; does it replicate on an independent task set; is the overall claim supported.
5. **Contributions**: (i) system + visibility-proof mechanism; (ii) preregistered confirmatory protocol with non-inferiority margin and full audit; (iii) independent 24-archetype task set with leakage audits; (iv) ablation + controlled fault-injection boundary; (v) cross-model direction check.

### 9.4 Related Work（结构；引用见 part6_literature_verified.md §10）

- **Agent memory**: hierarchical/virtual context (MemGPT), reflection buffers (Reflexion), skill libraries as executable memory (Voyager), surveys [2404.13501, 2605.06716] — mostly dialogue/QA; we target code workspaces and step-level delivery.
- **Long-context management & compression**: Lost in the Middle, RULER, LLMLingua, Selective Context, AGORA (agent action-grammar destruction) — compression is mostly token-level and unverified; we deliver at file/symbol granularity with a proof gate.
- **Coding-agent context acquisition**: SWE-bench/SWE-agent/AutoCodeRover/OpenHands; process-level retrieval benchmarks (ContextBench, ARB, SWE-Explore, CORE-Bench) measure recall/precision of exploration — we measure *end-to-end* cost/accuracy under a frozen non-inferiority protocol with delivery verification.
- **KV cache reuse & consistency** (boundary): vLLM/PagedAttention, SGLang/RadixAttention, Prompt Cache, CacheBlend, CacheTune, Irminsul — serving-side reuse with output-consistency concerns; **we make no KV-memory claims** (no tensor measurements).
- **Verifiable caching**: vCache (error-rate guarantees for semantic cache hits), prompt-cache auditing — verification targets cache *hit correctness*, not *final-message visibility of omitted context* (our O′ object differs).

### 9.5 Method（章节草案）

1. **System overview**: workspace index (files, symbols, digests), memory entries (static representations + decisions), planner (edit targets E, must-full closure, candidates), assembler (EXPAND/DIGEST/NONE + O′ omission with visibility proof), pre-send validation.
2. **Visibility proof (O′)**: each omission carries a check that no requirement signal in the current step references the omitted content; pre-send gate rejects insufficient plans (INSUFFICIENT/DHO accounting in results).
3. **Dual-token addressing** (supporting, not claimed standalone): static reusable representation × symbolic ID addressing — described as implementation detail; independent contribution **not** established (see §11).
4. **Baselines**: memory_off (full relevant injection without reuse), symbol_full_read (symbol-level full read without V12 reuse) — identical tasks/prompts/model/budget.

### 9.6 Experimental Setup

- **Preregistration**: independent prereg sha `7023da82…` (and parent P1 prereg `088898a3…`); frozen before any confirmatory request; exclusions/stop rules/NAs fixed.
- **Task suites**: (a) P1 confirmatory 48-task suite (8 parameterized families); (b) **independent-v1**: 48 tasks / 24 archetypes / 272 steps, cross-set hash & instruction overlap zero, forbidden-term scan zero, per-step discriminating evals (272/272), info points pre-declared (191).
- **Model/budget**: deepseek-v4.1-flash-1017, temperature 0, seed 0, max_tokens 2048 (P0-selected), history keep; R=5; randomization seeds 20261107 (P1) / 20261111 (independent).
- **Statistics**: task-cluster bootstrap (seed 20261102, B=10000), paired sign-flip, Holm over two primary pairs, non-inferiority margin −12 pp ESR, family/archetype sensitivity, failure disclosure.

### 9.7 Results（现有数据；独立集 [TBD]）

- **RQ1 (P1)**: prompt/episode −23.6% (F−memory_off), −24.2% (F−symbol_full_read); Holm p=0.0002; family-level 8/8 same sign.
- **RQ2 (P1)**: ΔESR −0.83 pp; CI lower bounds −4.2/−5.4 pp ≥ −12 pp → non-inferiority PASS.
- **Independent set**: [effect sizes + CI + Holm p + non-inferiority verdict — fill after Part4/Part5].
- **Cross-model (P3-A)**: 6/6 metrics same direction, non-inferiority PASS on qwen3.8-flash.
- **Difficulty strata & archetype sensitivity**: [tables from metrics_summary/family_sensitivity].
- **Failures**: full disclosure table (mechanisms: model_no_edit / noop / wrong implementation / protocol / infra) [fill].

### 9.8 Ablation (P2, confirmatory-mechanism)

- O′ off: −398 tokens/episode recovered (dominant saving) at unchanged ESR → mechanism attribution for RQ1.
- history redact: −350 tokens but CMR_visible −7.5 pp → correctness cost; not adopted as default.
- closure off: +24 tokens, zero ESR delta → small contribution.
- V13B no-body→NONE: no three-axis advantage → abandoned (also causally falsified in round3).

### 9.9 Security / Failure Boundary (VSO)

- Phase1 harness joint verdict PASS (UOR=0, SOR=1.0, FBR=0, FSR=1.0; EDR VSO=1.0 vs B1=0.0/B2=0.8; V4-exclusive detection=1).
- Phase2: 30/30 controlled fault-injection scenarios PASS, unsafe=0, DHO=0.
- **Wording constraint**: controlled injection results only — not production failure rates; not a universal safety guarantee.

### 9.10 Limitations

1. Main evidence on one model family (deepseek) + one cross-model direction check;
2. Effective independent designs = 24 archetypes (disclosed, sensitivity reported);
3. Protocol violations are budget-truncation driven (4096 retest: 86.3% resolved);
4. No KV-cache/tensor measurements → no memory-footprint claims;
5. Dual-token independent benefit unestablished;
6. temperature-0 server-side nondeterminism → R=5 is sampling repetition (disclosed);
7. Synthetic micro-repo tasks (both suites) — external validity to giant monorepos untested.

### 9.11 Conclusion

Structured, addressable code memory with visibility-proof selective delivery reduces multi-turn prompt cost by ~24% under a preregistered non-inferiority protocol, replicates direction on an independent 24-archetype task set [TBD final numbers], and is bounded by controlled fault injection; claims are scoped to prompt-cost and task-completion, not KV memory or unproven subcomponents.

### 9.12 图表规划

| 图/表 | 内容 | 数据源 |
| --- | --- | --- |
| Fig.1 | 三臂 ESR 总体+难度分层 | make_figures fig1 |
| Fig.2 | prompt/episode 分布 | fig2 |
| Fig.3 | 能力–开销权衡 | fig3 |
| Fig.4 | long 任务上下文增长曲线 | fig4 |
| Fig.5 | 逐任务配对差 | fig5 |
| Fig.6 | 失败机制 | fig6 |
| Fig.7 | archetype 敏感性 | fig7 |
| Tab.1 | 主结果（P1 + 独立集并排，同模型分列不合并） | metrics_summary + bootstrap |
| Tab.2 | 消融（P2 七臂） | p2 report |
| Tab.3 | VSO 边界 | vso_report |
| Tab.4 | 跨模型方向一致性 | direction_consistency.csv |
| Tab.5 | 失败全披露 | failure_analysis |

### 9.13 贡献声明（措辞红线）

- ✅ 可主张：prompt 开销下降（同模型、两任务集、CI+校正）；ESR 非劣（界值内）；O′ 主导机制（消融）；受控注入下证明门拦截 unsafe 省略。
- ❌ 不可主张：KV 显存下降；双 Token 独立收益；VSO 收益归因双 Token；30/30=普遍安全；跨模型绝对 token/ESR 合并。

---

## 10. 投稿期刊候选与风险评估（Part7）

判断依据：研究范围（SE 实证 + LLM agent 系统）、创新强度（机制+协议+独立复现）、实验完整性（预注册/消融/故障注入/跨模型）、以及各刊近期发表匹配度。**三档判断以独立集结果为准**——下表为候选池与预判，[独立集完成后定档]。

### 10.1 候选池（均为 SCI 收录的 SE/系统方向期刊）

| 期刊 | 匹配点 | 风险 | 预判档位 |
| --- | --- | --- | --- |
| **Empirical Software Engineering (EMSE)** | 实证方法、预注册协议、非劣设计、完整审计链——与本文方法论最契合 | 竞争激烈；要求实证严谨度高（我们强项） | [独立集 PASS → 可投] |
| **Journal of Systems and Software (JSS)** | 系统+实证混合；LLM agent 工程实践接受度上升 | 创新声明需克制（组件非全新） | [可投/需补] |
| **Information and Software Technology (IST)** | AI for SE、工具与实证 | 影响因子中档；需突出工程意义 | [可投] |
| **Automated Software Engineering (Springer, ASE 期刊版)** | agent/自动化主题直接匹配 | 篇幅与新颖性门槛 | [需补实验/可投] |
| **IEEE Transactions on Software Engineering (TSE)** | 顶刊；系统+实证兼备 | 单模型族主证据可能被视为广度不足；周期长 | [需补实验：加第三模型或大规模真实仓库] |
| **ACM TOSEM** | 系统与实证 | 同 TSE，广度要求高 | [需补实验] |

### 10.2 档位规则（结果出来后套用）

- **可投稿**：独立集 RQ1 显著且方向与 P1 一致 + RQ2 非劣 PASS + 失败披露完整 → 首选 EMSE（或 JSS 备选）。
- **需补实验**：独立集效应量明显缩水或非劣 CI 贴边、或审稿人可合理要求第三模型/真实仓库 → 先补（追加 qwen 确认或 monorepo 外部效度小实验）再投 TSE/TOSEM。
- **不建议投稿**：独立集 RQ1 不显著或 RQ2 非劣失败 → 不包装；回到边界如实报告，仅投 workshop/短文或重构主张后重做。

（最终判断在 §12 给出，依赖 §5–§7 全部结果。）

---

## 11. 全部局限、偏差与未解决问题

1. **D1–D10 历史偏差**（§1.5）——全部保留原始记录，处置可追溯；
2. **有效独立设计数**：independent-v1=24 archetype×2 变体（披露族敏感性；下界 24、上界 48）；
3. **双 Token 独立贡献未证实**——仅作机制专项报告（`dualtoken_ablation`），不进论文主主张；
4. **KV Cache 显存**：无张量实测，禁止任何显存下降主张；
5. **协议违规复测**：4096 下 86.3% resolved、2 集仍触顶——归因于输出预算而非架构；
6. **VSO 30/30**：受控注入结果，不得描述为生产自然故障率或普遍安全保证；
7. **非确定性**：temperature=0 下服务端生成仍抖动（round2/3 实测），R≥5 的实质=采样重复（如实披露）；
8. **单端点单模型家族**：主结论限于 deepseek（P3-A 仅方向性佐证）；
9. **未解决问题清单**（延续）：VSO §11 歧义默认值；RAG 综述等少量文献 DOI 待补（不影响主张）。

---

## 12. 最终投稿准备度结论

（待全部实验与统计完成后给出：可投稿 / 需补实验 / 不建议 三档结论与理由。）

---

### 附录：冻结哈希总表（写入即用）

| 物件 | sha256 |
| --- | --- |
| P1 预注册 | `088898a3aec9d08411864ea03ff79ac7ff3e78411ed34a58de89ecd0881cc7ed` |
| Part3 独立集预注册 | `7023da82be3fb9892434ca183749a8bd6b854f660842e8e809836d3baf495a33` |
| Part2 设计文档 | `d757993d235193cae470c9d172dee13293e13640f9007a7010a1e52af666bb91` |
| P3-A 补记 | `2ce8defff22395fcfe7d48325a7c9f9fc5cd8c867b7f8be7643833dd2e38fffe` |
| VSO 设计 v2 | `0d9c292b2ef7e09fc0d6ddef137d163ca91a342c1e8144341fce3d3725f1746b` |
| 双 Token 补记 | `d664d602fc3c82a9494c4eed7108e22f5ac272bff41ae732414ef3d60aa2a088` |
| independent_tasks.json | （任务集冻结时回填） |
| independent_tasks_manifest.json | （任务集冻结时回填） |
