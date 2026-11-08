# V1.3-M2 Validation Plan REV3（M2-Revision-Fix）

状态：**完整计划**。关闭 `v13_m2_revision_review_report.md` 的 R1–R6。  
继承：原计划 `v13_m2_validation_plan.md` → rev2 → **本 rev3**。  
本阶段仅改设计文档；**不建 Holdout、不改代码、不跑模型、不改 Git**。

**冻结不变**：V13A 算法；E/F/V13A；12 全新 holdout（不足则 8）；R=2；72 episodes / ≈144 requests；Q6_K+llama；ET/C/must/O′/INSUFFICIENT；ESR/TPAE/TPSE 阈值；无额外模型调用/自动重试/反馈环。

---

## 0. 修订索引

| R | 问题 | rev3 处理 | 章节 |
| --- | --- | --- | --- |
| **R1** | bootstrap seed 冲突 | **恢复 20261102**；B=10000；task cluster 不变 | §3.3、§4.3 |
| **R2** | S7 不可执行 | **方案 B：降级为诊断观察，不参与自动停止** | §5.2 |
| **R3** | Prompt 冻结不足 | SYSTEM_PROMPT + `build_messages` 双哈希 + 消息顺序 | §3.1.1 |
| **R4** | 字段字典不全 | 字段字典（类型/来源/时点/缺失/指标） | §3.3.1 |
| **R5** | 错误分类 | 四类矩阵 + ESR/S4/重试/有效性 | §4.5 |
| **R6** | 失败率窗口与状态枚举 | S4=全 run；状态五定义 | §5.2.1、§4.6 |

---

## 1. V13A 机制（不变）

```text
related → FULL iff implementation_body ∧ (instruction_hit ∨ dependency_touch)
否则 DIGEST；body 不可算 → 保守 DIGEST
ET/C/must → 始终 FULL
```

审计：`adaptive_audit`（path, body, hit, touch, level, reason）。

---

## 2. Holdout

- 首选 **12** 新任务；不足 **8**；**禁止**旧 24 冒充。  
- 路径 `p1/tasks_v13_holdout/`；`holdout_manifest.json`（id/type/instruction_sha/files_sha/eval_sha）。  
- 与 v1 业务文件 hash 交集为空。  
- **同源（R 补强）**：每 task 单一 `project/` → E/F/V13A 各自 `copy`；禁跨臂复制；step2 仅本臂。

---

## 3. 实验设计

### 3.1 臂与环境（不变）

| 臂 | related |
| --- | --- |
| E | digest |
| F | full |
| V13A | adaptive_a |

Q6_K · ctx8192 · parallel1 · seed0 · temp0 · max_tokens1024 · keep · d=2 · Kmax=8。

#### 3.1.1 Prompt 与消息冻结（R3）

| 项 | 冻结值 | 核验 |
| --- | --- | --- |
| SYSTEM_PROMPT 文件 | `p1/scripts/p1_common.py::SYSTEM_PROMPT` | — |
| SYSTEM_PROMPT sha256 | **`4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a`** | **实测一致** |
| `p1_common.py` 整文件 sha256（**read_bytes 原始字节**） | **`e32fd30517322e8976c8f7710be69fae508c9957a926079c526f9468a3f384f2`** | **实测 bytes**；**不用** `read_text().encode()` |
| `build_messages` 函数源码 sha256 | **`f0b477b0046282739ba1309e5035b2beb2f2f8d2564535d7154019a9aee9e436`** | `inspect.getsource` 实测 |
| 代码位置 | `p1_common.py` L615–626（`build_messages`） | 实测 |

**消息构造顺序（冻结）**：

```text
messages = history + [user]
history  = [system] + 过往 assistant 消息序列（仅 assistant；见 runner append）
user     = "=== TASK ===\n{instruction}\n\n=== CONTEXT ===\n{context}\n\n=== OUTPUT FORMAT ===\nRespond only with FILE: blocks (or NO_EDIT)."
roles    : system | assistant | user
```

**history=keep**：`trim_history` 预算默认 24000 字符；keep=不主动丢弃（与 P1 `--history-policy keep` 一致）；**不**在 holdout 实验中切换 redact。

**文件注入位置**：仅 `user.context` 内 `--- FILE path (full current source) ---` 块；assistant 侧为模型 `FILE:` 围栏回写。

开跑：`run_meta` 记录 `system_prompt_sha256`、`build_messages_source_sha256`、`p1_common_sha256`；任一不一致 → **停**。

### 3.2 规模（不变）

12×3×R=2 = **72 eps · 144 requests**。  
R=3 触发：\|ΔESR(V13A−E)\| 点估计 &lt;5pp 且 CI 宽（原规则）。

### 3.3 随机化与统计 seed（R1 修复）

| 项 | 值 |
| --- | --- |
| 随机化执行顺序 seed | **20261103**（episode 排序，写入 randomization_manifest） |
| **Bootstrap seed** | **20261102**（与 V1.2 prereg §7 **一致**） |
| Bootstrap B | **10000** |
| 聚类单位 | **task_id**（同 task 全部 rep+全部臂） |

**依据**：prereg 冻结 bootstrap seed=20261102；rev2 误用 20261103 且无变更记录 → **rev3 纠正**。  
分析脚本须写 `bootstrap_seed=20261102` 于 analysis_manifest。

输出根：`p1/experiments/v13_holdout_validation/`。  
超时 300s/步；**无自动重试**。

#### 3.3.1 字段字典（R4）

| 字段 | 类型 | 来源 | 时点 | 缺失 | 指标 |
| --- | --- | --- | --- | --- | --- |
| eval_success | 0/1 | eval_output→result | 步末 | 记 error，计失败步 | ESR/SPR |
| prompt_tokens | int | request/usage | API 返回 | 0+error | Prefill \(P_s\)、TPAE/TPSE |
| completion_tokens | int | usage | API | 0 | 同上 |
| total_tokens | int | P+C | 步末 | 0 | TPAE/TPSE/FETC |
| context_file_blocks | int | context.txt 计数 | 装配后 | 0 | Full 计数 |
| context_digest_lines | int | context.txt `--- INDEX` | 装配后 | 0 | Digest 计数 |
| must_full_count | int | plan.audit | 装配后 | 0 | must 完整 |
| edit_targets | str[] | plan/targets | 装配后 | `[]` | 安全 |
| adaptive_audit | obj[] | plan | 装配后 | `[]` | 升级率 |
| insufficient | 0/1 | ctx/plan | 发送前 | 0 | INSUFFICIENT |
| pre_send_check.ok | bool | verify | **发送前** | 缺文件→fail | VP/阻断 |
| DHO | 0/1（可由 audit 导出） | omitted∩edit_targets 事后核对 | 步末 | 缺 audit→**不可算记 NA** | DHO |
| O′/vproof | pre_send + omitted_files | injection_audit | 发送前 | 缺→NA | VP |
| error | str | runner | 步末 | `""` | 错误分类 |

**说明**：DHO/RSR/ISR 若日志未直接给字段，由 `omitted_files`×`edit_targets`×`pre_send` **导出**；导出脚本须与结果一并存档。  
**已核实存在**：pre_send_check、injection_audit、result 中上述键（与 P1/v12 runner 一致）。**未实现字段不得写成已存在**——上表“导出”项标注来源。

### 3.4 指标

| 指标 | 定义 |
| --- | --- |
| ESR / SPR | 同 V1.2 method |
| TPAE / TPSE / FETC | method §1.3；零成功 TPSE=**NA/∞**；零失败 FETC_mean=**NA** |
| Prefill | **= prompt_tokens**；cached 分列；**禁止** KV 节省表述 |
| Full/Digest/None 率 | context 计数 / 步 |
| 升级率 | related 中升 Full / related 评估数；原因 hit/touch/body |
| DHO/RSR/ISR/INSUFFICIENT | method/prereg + §3.3.1 导出 |

---

## 4. 成功与分类

### 4.1 安全一票否决（不变）

VP 无违规放行；must 无丢失/降级；DHO=0；INSUFFICIENT→请求 0。

### 4.2 效果点估计（不变）

ESR(V13A)≥ESR(E)−0.05；≥ESR(F)−0.05；TPAE≤F；目标≤E×1.02。

### 4.3 统计

task 聚类；bootstrap **seed=20261102** B=10000；R=2 探索性；72≠独立任务数。

### 4.4 报告纪律

NOT_TRIGGERED≠PASS；协议错误≠架构；TPSE 与 TPAE 同报。

### 4.5 错误分类矩阵（R5）

| 类 | 定义 | 计入 ESR | 计入失败率(S4) | 重试 | 保留记录 | 影响 episode |
| --- | --- | --- | --- | --- | --- | --- |
| **protocol** | 模型非 FILE/NO_EDIT 或违格式 | **是**（步 fail） | 是（episode 失败） | **否** | 是 | 无效步 |
| **architecture** | VP 违规仍请求、must 丢失、静默截断等 harness 安全/逻辑错误 | **是**（且安全停机 S1） | 是 | **否** | 是 | 标记 invalid；**停机** |
| **task** | 任务规格/eval 自身矛盾（预注册任务设计问题） | 是 | 是 | 否 | 是 | 保留但标注；**不得**剔除美化 ESR |
| **infrastructure** | HTTP 超时/磁盘/server 拒绝 | 是 | 是 | **否**（无自动重试） | 是 | error 非空 |

**待决（原始设计未写死，不发明）**：

| 项 | 状态 |
| --- | --- |
| infrastructure 连续失败是否允许人工单次重跑 | **待决**（当前默认禁止自动重试；人工重跑须单独批准并记 audit） |
| task 设计问题是否从 ESR 剔除 | **否**（默认计入）；剔除须预注册变更 |

协议违规 **不得** 直接写成 architecture failure；architecture failure 必须 S1 停机。

### 4.6 状态枚举（R6）

| 状态 | 定义 |
| --- | --- |
| **PASS** | 步/机制/门禁按定义成功 |
| **FAIL** | 已执行且未达定义 |
| **NOT_TRIGGERED** | 机制未发生（≠PASS） |
| **NOT_APPLICABLE** | 该任务/臂不适用 |
| **INSUFFICIENT** | 请求前上下文/验证不足，**未**发模型请求 |
| **NA** | 指标无定义（零分母等）；**≠0** |

---

## 5. 成本与停止

### 5.1 预算（不变）

72 eps · 144 req · ≈4min · ≈42k tokens（est）。

### 5.2 停机表（R1/R2/R6）

| # | 条件 | 动作 |
| --- | --- | --- |
| S1 | 安全违规（§4.1） | 立即停 |
| S2 | 磁盘&lt;2GB / server 拒绝 | 停 |
| S3 | Holdout 冻结失败/与 v1 泄漏 | 停 |
| S4 | 失败率&gt;50%（§5.2.1） | 查 harness |
| S5 | Token &gt;2× 计划 | 停 |
| S6 | ESR(V13A)&lt;ESR(E)−0.10 **且** TPAE(V13A)≥TPAE(F) | 停扩展 V13A |
| **S7** | **诊断观察（不参与自动停止）** | 见 §5.2.2 |

#### 5.2.1 S4 窗口与失败率（R6）

- **窗口 = 整个 run**（全部已尝试 episode），非滚动窗。  
- 失败率 = 失败 episode / 尝试 episode。  
- “非模型 NO_EDIT”观察 = 失败步中 harness/infrastructure 类占比（§4.5），**无新百分比门**。  
- 不新增阈值。

#### 5.2.2 S7 诊断观察（R2 方案 B）

**原 S7（升级率极端）证据不足**（无预注册可计算阈值）→ **不参与自动停止**。

**保留为分析输出**（不判定通过/失败）：

| 记录项 | 单位 | 方法 |
| --- | --- | --- |
| related Full 比例（V13A vs E vs F） | 每臂：升 Full 的 related 文件数 / related 评估数（按 step 汇总） | 描述统计 |
| hit/touch 升级占比 | **单位 = adaptive_audit 行（每文件×步）** 中 reason 含 hit 或 touch 的比例 | 描述统计 |
| 分布比较 | 与 E/F 的 Full 比率并排表 | **无**假设检验、**无**自动停机 |
| 样本不足 | n 小则只报计数 | 不写显著 |

**禁止**：将 S7 描述为统计检验通过/失败；用 S7 单独停 run（停机仅 S1–S6）。

### 5.3 开跑前

rev3 sha + bootstrap_seed=20261102 写入 run_meta/analysis_manifest；禁止结果后改 S1–S6。

---

## 6. 本地/云（不变）

1.5B 本地探索；租云前接口/token/模型 id（原 P0 项）；本阶段不租云。

---

## 7. 路线（不变）

rev3 独立审查通过 → **M2-Holdout Freeze**（单独授权）→ 本地 E/F/V13A×12×R2 → 探索报告。

**停扩展 V13A**：S1 或 S6（**不含 S7**）。

---

## 8. 边界

仅新增本文件 + `v13_m2_revision_fix_response.md`。未改代码/任务/rev2/原计划/Git/模型。
