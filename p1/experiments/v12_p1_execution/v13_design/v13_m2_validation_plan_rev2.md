# V1.3-M2 Validation Plan REV2

状态：**M2-Plan Revision 修订稿**（关闭 `v13_m2_review_report.md` 中 P1）。  
原计划：`v13_m2_validation_plan.md`（只读保留，不覆盖）。  
本阶段：**不建 Holdout、不改代码、不跑模型、不改 Git**。

**未改变（与 rev1 冻结一致）**：V13A 算法、E/F 臂定义、12×3×R=2 样本量原则、r2.2 安全门槛、停止阈值数值（§7 原有条件原样纳入，不新造）。

---

## 0. 修订对照（关闭审计 P1）

| ID | 审计问题 | rev2 关闭方式 | 章节 |
| --- | --- | --- | --- |
| P1-01 | §5.3 与 §7 停机不一致；升级率未量化 | §5.3 **并入**原 §7 全部条件；升级率改为 **诊断报告项（非停机）**，不新增停机阈值 | §5.3、§7 |
| P1-02 | 未规定 task 聚类 | 报告以 **task 为聚类单位**；task-cluster bootstrap B=10000 seed=**20261103**（与随机化 seed 区分见 §3.3） | §3.4、§4.3 |
| P1-03 | SYSTEM_PROMPT 未冻结 | 锁定 `p1_common.SYSTEM_PROMPT` **sha256=`4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a`** + `build_messages` 模板 | §3.1.1 |
| P1-04 | per-step 字段不全 | §3.3.1 字段清单（与 P1 同级） | §3.3.1 |
| P1-05 | 同源初始快照 | §2.4：同 task 三臂均 copy 同一 holdout 冻结 `project/` | §2.4 |
| P1-06 | Prefill 未定义 | Prefill 主指标 = API `prompt_tokens`（\(P_s\)）；`cached_tokens` 分列 | §3.4.1 |
| P1-07 | 零成功/零失败 NA | 交叉引用 method §1.3 / prereg（TPSE=NA/∞；FETC_mean=NA） | §3.4.2 |
| P1-08 | NOT_TRIGGERED≠PASS | 报告纪律 | §4.4 |
| P1-09 | 协议错误≠架构 | 报告纪律 | §4.4 |
| P1-10 | 失败率>50% 模糊 | **改为诊断口径定义**（非新停机阈值）；原句保留为“观察项” | §5.3 |

**明确未改**：V13A 规则、臂集合、R=2 首选、12/8 Holdout 规则、安全一票否决、§7 原停止条件数值。

---

## 1. V13A 机制（不变，摘要）

```text
related → FULL iff implementation_body ∧ (instruction_hit ∨ dependency_touch)
否则 DIGEST；body 不可算 → 保守 DIGEST
ET/C/must → 始终 FULL
```

审计字段：`adaptive_audit`（path, body, hit, touch, level, reason）。  
与 E/F 差异及决策链见 rev1 §1 与 M1 审计（**未改算法**）。

---

## 2. Holdout 任务（方法不变 + P1-05）

### 2.1 规模

- **首选 12** 新任务；不足 → **8**；**禁止**旧 24 冒充独立验证。  
- 类型配额（S/M/D/R/I/X）与难度分布同 rev1；禁按预期胜负挑选。

### 2.2 冻结

- 路径：`p1/tasks_v13_holdout/`（或等价）；**不改** `tasks_v1.0.json`。  
- `holdout_manifest.json`：id、type、instruction_sha、project_files_sha256、eval_sha。  
- 与 v1 24 任务业务文件 hash **交集为空**；禁抄指令/CFD03 实现。

### 2.3 三臂同源（关闭 P1-05）

对每个 `task_id`：

```text
source = holdout/<task_id>/project   # 单一冻结源
E   → copy(source) → workspaces/<task>_E_R<r>/
F   → copy(source) → workspaces/<task>_F_R<r>/
V13A→ copy(source) → workspaces/<task>_V13A_R<r>/
```

**禁止**从其他臂工作区复制；step2 仅用本臂本 episode 的 step1 结果。

---

## 3. 实验设计

### 3.1 臂与环境（不变）

| 臂 | related |
| --- | --- |
| E | digest |
| F | full |
| V13A | adaptive_a |

Q6_K · llama-server ctx=8192 parallel=1 · seed=0 temp=0 max_tokens=1024 · history=keep · d=2 · Kmax=8。

#### 3.1.1 Prompt 冻结（关闭 P1-03）

| 项 | 冻结值 |
| --- | --- |
| SYSTEM_PROMPT | `p1/scripts/p1_common.py::SYSTEM_PROMPT` |
| SYSTEM_PROMPT sha256 | **`4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a`**（UTF-8） |
| 用户消息模板 | `build_messages()`：`=== TASK ===` / `=== CONTEXT ===` / `=== OUTPUT FORMAT ===`（**不得**改模板） |
| 系统消息 role | `system`；其余 history 沿用 runner 现行逻辑 |

开跑前：run_meta 记录 `system_prompt_sha256`；不一致 → **停**。

### 3.2 规模（不变）

**12 × 3 臂 × R=2 = 72 episodes · 144 requests**（每 episode 2 步）。  
R=3 触发：R=2 后 V13A vs E 的 \|ΔESR 点估计\| &lt; 5pp 且 CI 宽（**原规则，未改**）。

### 3.3 随机化与隔离（不变 + 字段）

- 随机化 seed：**20261103**；bootstrap seed：**20261103**（统计重采样可与随机化同值，**记录于 analysis_manifest**；若需分离仅改 bootstrap 记录字段并预注册，**不得**事后改）。  
  **审计 P1-02 要求聚类 bootstrap**；为避免“新统计检验”，采用与 P1 相同方法：task 聚类、B=**10000**、percentile 95% CI——**方法沿用 P1**，非新检验设计。  
- 输出：`p1/experiments/v13_holdout_validation/`  
- 每步超时 300s；**无自动重试**；异常记 error。

#### 3.3.1 Per-step 必存字段（关闭 P1-04）

每 episode×step 至少：

`context.txt`, `messages.json`, `pre_send_check.json`, `injection_audit.jsonl`, `response.txt`, `eval_output.txt`, `result.json`, `request.json`

`result.json` 至少含：episode/task/arm/rep/step、eval_success、prompt/completion/total_tokens、context_file_blocks、context_digest_lines、must_full_count、edit_targets、insufficient、error、adaptive_audit（或注入 audit 内）。

每 episode：`workspace_pre_manifest.json` / `post` / `diff`。

### 3.4 指标（关闭 P1-06、P1-07）

#### 3.4.1 主指标

| 指标 | 分子/分母 | 来源 |
| --- | --- | --- |
| ESR | 两步全过的 episode / 臂内 episode | eval |
| SPR | 通过步 / 总步 | eval |
| TPAE | ΣT(e) / 尝试 episode 数 | result tokens |
| TPSE | ΣT(e) / 成功 episode 数 | 同上 |
| FETC_total / mean | 失败 ΣT；失败均值 | method §1.3 |
| **Prefill** | **主指标 = API `prompt_tokens`（\(P_s\)）** | usage |
| cached_tokens | **仅分列**；**禁止**作 KV/显存节省 | usage 可选 |

#### 3.4.2 边界与缺失（关闭 P1-07）

- 成功数=0 → TPSE = **NA/∞**（不得记 0）  
- 失败数=0 → FETC_mean = **NA**  
- 缺 step/缺 token → 记 `error`，计入尝试分母，**不删任务**  
- 以 **`v1.2_method_formulation.md` §1.3** 与 prereg 为准；本节不另立第三定义  

#### 3.4.3 机制与安全指标

Full/Digest/None 计数与比例；V13A 升级率 = #related 升 Full / #related 评估数；升级原因分布（hit/touch/body）。  
DHO、RSR、ISR、INSUFFICIENT、must 完整、请求前阻断次数：定义见 **V1.2 method/prereg**（本计划交叉引用）。

---

## 4. 成功标准

### 4.1 安全（一票否决，与 rev1 相同）

VP 无违规放行；must 无丢失/降级；DHO=0；INSUFFICIENT 时请求=0。  
任一失败 → 整体不成功。

### 4.2 效果（点估计；数值与 rev1 相同，未改）

- ESR(V13A) ≥ ESR(E)−0.05  
- ESR(V13A) ≥ ESR(F)−0.05  
- TPAE(V13A) ≤ TPAE(F)；目标 ≤ TPAE(E)×1.02  
- 分配有意义：升级主要来自 hit/touch+body  

### 4.3 统计解释（关闭 P1-02）

- **推断/聚类单位 = task_id**（同 task 全部 rep、全部臂一并重采样）。  
- 72 episodes **不是** 72 个独立任务。  
- task-cluster bootstrap：B=10000，seed=20261103，percentile 95% CI；**方法与 P1 相同**。  
- R=2 结果 = **探索性**；CI 宽则只报点估计方向。  
- **禁止**：单任务胜负作结论；“统计显著/证明有效/已证非劣”（除非独立更大样本且预注册检验）。

### 4.4 报告纪律（关闭 P1-08、P1-09）

- `NOT_TRIGGERED` **不得**计为机制 PASS。  
- 模型 NO_EDIT / 推理错误 → 归 **模型能力**，不得直接记为记忆架构失败。  
- TPSE 必须与 TPAE 同报。

---

## 5. 成本与停止条件

### 5.1 预算（沿用 rev1 est，未改）

12×3×R2：72 eps · 144 请求 · ≈4 min · ≈42k tokens（est，基于 P1 实测外推）。

### 5.2 执行停机表（关闭 P1-01：与原 §7 对齐，**不改数值**）

| # | 条件 | 来源 | 动作 |
| --- | --- | --- | --- |
| S1 | 安全违规（§4.1） | 原 §4.1/§5.3 | **立即停** |
| S2 | 磁盘&lt;2GB 或 server 拒绝连接 | 原 §5.3 | 停 |
| S3 | Holdout 冻结失败 / 与 v1 泄漏 | 原 §5.3 | 停，不跑 |
| S4 | 单 episode 失败率&gt;50%（见下口径） | 原 §5.3 | 查 harness |
| S5 | Token 预算 &gt;2× 计划 | 原 §5.3 | 停，复盘 |
| S6 | **ESR(V13A) &lt; ESR(E)−0.10 且 TPAE(V13A) ≥ TPAE(F)** | **原 §7** | **停止扩展 V13A**（研究判定停机） |
| S7 | V13A 升级率极端且无 hit/touch 区分 | **原 §7** | **停止扩展 V13A**（研究判定停机） |

**S4 口径（关闭 P1-10，不设新阈值）**：  
失败率 = 失败 episode / 尝试 episode；“且非模型 NO_EDIT”指：失败步中 **非** `NO_EDIT` 且 **非** 已归类模型推理错误的 **harness/系统错误**（error 非空、eval 环境崩溃等）占失败步比例——仅用于 S4 观察，**不**另设百分比新门。

**S7 口径（不新增数字阈值）**：  
“极端且无区分” = 报告中 V13A related 升级率使 **V13A 与 F 的 Full/Digest 分布几乎不可区分** 或 **与 E 不可区分**，且 adaptive_audit 的 hit/touch 触发占比无法解释差异——由分析脚本给出分布后人工按此定义判定；**不**在计划中写死 90%/10% 等新数字。

**开跑前**：本表 sha 随 run_meta 冻结；禁止结果出来后改 S1–S7。

---

## 6. 本地模型 / 云端（沿用 rev1 §6，未改 P0/P1/P2 分级）

1.5B 适合本地探索；租云前完成接口可配置、token 映射、模型 id 记录；首次云请求做计数校准；VP/ET/must 与后端无关。  
**本阶段不租云。**

---

## 7. 推荐路线（不变）

1. 本 rev2 审计通过 → **M2-Holdout Freeze**（建任务，仍需单独授权）  
2. 本地 E/F/V13A × 12 × R=2  
3. 探索性报告（task 聚类 + 安全一票否决）  
4. 再议 R=3 / 云  

**停止 V13A**：S1 或 S6 或 S7。

---

## 8. 本阶段边界

- 仅新增本文件与 `v13_m2_revision_response.md`  
- 未改原计划文件、代码、任务、Git、模型  

等待 M2-Revision Review。
