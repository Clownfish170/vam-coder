# V1.3-M2：Adaptive Full/Digest Independent Validation Plan

状态：**规划文档（只读分析）**。不改代码、不跑模型、不申请云端、不操作 Git。  
唯一交付物：本文件 `p1/experiments/v12_p1_execution/v13_design/v13_m2_validation_plan.md`。  
依据：`v13_m1_final_audit.md`、P1 `execution_summary.json` / `per_step_all.csv`、`adaptive_features.py` / `levels.py`。

---

## 1. V13A 行为分析（代码事实 / 数据 / 假设）

### 1.1 决策链（代码事实）

```text
build_plan (levels.py):
  1) EditTargets / CandidateFull → 强制 FULL（先于 adaptive）
  2) must_full（含 dep/closure）→ FULL
  3) 仅 policy==adaptive_a 且 r≥1 的相关非目标 → decide_related_level()
       FULL iff implementation_body ∧ (instruction_hit ∨ dependency_touch)
       否则 DIGEST；body 不可算 → 保守 DIGEST
  4) 无关 → non_target_unrelated=none → NONE
```

| 组件 | 路径 | 事实 |
| --- | --- | --- |
| AST 实现体 | `adaptive_features.has_implementation_body` | FunctionDef/Async/Class → True；SyntaxError → None |
| 指令命中 | `instruction_hit` | basename/stem/symbols 词边界；**plan 传 symbols=None**（仅路径/stem） |
| 依赖触达 | `dependency_touch` | provider+caller BFS，depth=`closure_depth`(2) |
| 审计 | `plan.adaptive_audit` | 每文件 body/hit/touch/level/reason |

### 1.2 dependency_touch 与 must 重叠（代码事实）

- `build_plan` 的 must 已含 **dep∪callers 闭包**（与 touch 同 depth=2）。  
- 因此 **provider 闭包内文件通常已 must→FULL**，不会进入 adaptive 分支。  
- 非 must 相关文件的 `dependency_touch` 多为 False → 实际升级主要靠 **instruction_hit**。

### 1.3 symbols=None（代码事实）

- `levels.py` 调用 `decide_related_level(..., symbols=None)`。  
- 符号级命中 **未接入** plan；仅路径/stem。

### 1.4 与 E/F 的理论差异

| | related 策略 |
| --- | --- |
| E | 恒 Digest |
| F | 恒 Full |
| V13A | 条件 Full（body ∧ (hit∨touch)），否则 Digest |

### 1.5 数据观察（P1，非 V13A 实测）

- 24 任务上 F 相对 E：ESR 约 +4.2pp，几乎全在 **CFD03**；TPAE +0.8%（`ef_diagnosis`）。  
- **无** V13A 运行数据（M1 未跑实验）。

### 1.6 待验证假设（非事实）

| 假设 | 状态 |
| --- | --- |
| H1: V13A 在新任务上 ESR ≥ E − ε | **待验** |
| H2: V13A TPAE ≤ F 且接近 E | **待验** |
| H3: CFD03 类“实现体+指令命中”在新任务可复现升级 | **待验** |
| H4: symbols 接入可减少漏升 | **待验**（M1 NB1） |

---

## 2. 独立任务集设计（12 个新任务）

**原则**：原 24 任务已参与规则启发 → **不得**作独立确认证据；仅作探索回归。

### 2.1 任务来源

- **新建** `p1/tasks_v13/`（或 `p1/tasks/v13_holdout/`），**不**改 `tasks_v1.0.json`。  
- 每任务：`project/` 初始代码 + `eval/step*` + JSON 元数据（instruction、expected_files）。  
- **冻结前**：目录 sha256 + 清单；与 v1 集 **文件级不重叠**（见 §2.4）。

### 2.2 12 任务清单（按类型，非按预期胜负）

| ID | 类型 | 覆盖 |
| --- | --- | --- |
| v13_S01 | 单文件编辑 | 基线 ESR |
| v13_S02 | 单文件边界 | 边界条件（空/负值/异常） |
| v13_M01 | 双文件无强依赖 | Digest vs Full 无 dep |
| v13_M02 | 双文件弱命名相关 | 指令歧义 |
| v13_D01 | 显式 import 依赖 | dependency_touch |
| v13_D02 | 两层调用链 | depth=2 |
| v13_D03 | 依赖+边界值 | 实现细节 |
| v13_R01 | 数据结构（dict/list） | 状态/结构 |
| v13_R02 | 类型/契约约束 | 接口 vs 实现 |
| v13_I01 | 相关文件含关键实现体 | **不**预设 F/V13A 必胜 |
| v13_I02 | 相关文件仅常量/辅助 | 预期偏 Digest |
| v13_X01 | 多模块协作（3 文件） | 跨文件 |

**难度分布**：短/中/长各约 4；与 CFD03 **同型仅 1–2 个**（I01），禁止全库同型。

### 2.3 选择偏差控制

- 类型配额在写任务 **之前** 固定。  
- 禁止：按 E/F/V13A 预跑结果挑任务。  
- 冻结：`holdout_manifest.json`（id、type、files_hash、instruction_sha）。

### 2.4 独立性检查

| 检查 | 方法 |
| --- | --- |
| 与 v1 24 任务文件 hash 交集 | 必须为空（或仅公共 stdlib 无业务） |
| 函数名/常量抄写 | 禁止直接复制 CFD03/RUR02 实现 |
| 指令模板 | 不得逐字复用 v1 指令 |
| 评估 | 行为断言 only；与 v1 风格一致但独立目录 |

### 2.5 规模

若 12 个合格任务无法在冻结前完成 → **降到 8**，并停止宣称“12 任务独立验证”；**禁止**用旧 24 冒充。

---

## 3. 最小实验设计

### 3.1 臂（3）

| 臂 | ID | related |
| --- | --- | --- |
| E | Digest 基线 | digest |
| F | Full 基线 | full |
| **V13A** | adaptive_a | adaptive_a |

环境：与 P1 相同（Q6_K、ctx8192、parallel1、seed0、temp0、max_tokens1024、keep、d=2、Kmax=8）。  
安全：ET/C/must/VP/INSUFFICIENT 与 r2.2 相同。

### 3.2 规模选择

| 方案 | Episodes | 约请求 | 建议 |
| --- | --- | --- | --- |
| **12 新 × 3 臂 × R=2** | **72** | **144** | **首选** |
| 12 × 3 × R=3 | 108 | 216 | 若 R=2 方向模糊且预算允许 |
| 24 × 3 × R=2 | 144 | 288 | 仅当需更大任务面且 **新任务** 24 个可冻结 |

**R=2→R=3 时机**：R=2 后若 V13A vs E 的 ESR 点估计 |Δ|<5pp 且 CI 宽，再升 R=3；否则停在 R=2 作探索。

### 3.3 随机化与执行

- 独立 `randomization_manifest`，**seed=20261103**（区别 P1 的 20261102）。  
- 输出根：`p1/experiments/v13_holdout_validation/`（**不**写入 P0/P1 目录）。  
- 隔离：每 episode 独立 workspace + pre/post/diff（复用 `workspace_audit` 模式）。  
- 超时：单步 300s；异常记 error，**不**自动重试刷成功。  
- 规则冻结：M1 算法在开跑前 sha 锁定；**禁止**按结果改规则。

### 3.4 指标

| 类 | 指标 |
| --- | --- |
| 主 | ESR、SPR、TPAE、TPSE、FETC_total/mean |
| 策略 | Full/Digest 计数与比例；V13A 升级率；升级原因分布（hit/touch/body） |
| 安全 | ET/C FULL、VP pre_send、DHO、INSUFFICIENT、must 完整、阻断请求=0 |
| 其它 | prompt/completion tokens；**cached_tokens 不作 KV 节省** |

报告纪律：TPSE 与 TPAE **同报**；低样本只作 **探索性**；点估计与 CI 分列。

---

## 4. 成功标准

### 4.1 安全（一票否决）

| 项 | 标准 |
| --- | --- |
| VP | 无“验证失败仍请求” |
| must_full | 无丢失/降级 |
| DHO | **0** |
| INSUFFICIENT | 请求次数 **0** |

任一失败 → **整体不成功**，停止扩展。

### 4.2 效果（相对 E / 相对 F，探索性）

| 门槛 | 定义 |
| --- | --- |
| 非劣 E | ESR(V13A) ≥ ESR(E) − 0.05（点估计；CI 另报） |
| 不劣于 F 过多 | ESR(V13A) ≥ ESR(F) − 0.05 |
| 成本 | TPAE(V13A) ≤ TPAE(F)；目标 TPAE(V13A) ≤ TPAE(E)×1.02 |
| 实现细节 | I01/D0 类：V13A Full 升级率合理且 ESR 不低于 E |
| 分配有意义 | 升级主要来自 hit/touch+body，而非全库 Full |

样本不足 → 只写“探索性方向”，**不写**显著/证明。

---

## 5. 成本预算

### 5.1 P1 实测（依据）

| 项 | 值 | 来源 |
| --- | --- | --- |
| Episodes | 504 | execution_summary |
| 总 tokens | 304,807（prompt 258,358 + completion 46,449） | per_step_all |
| 单臂平均 total/step | E 289.7 · F 292.0 · 其它 287–323 | 同上 |
| 墙钟 | 05:23–05:50 UTC ≈ **27 min** / 504 eps | execution_log |
| 单 episode 均时 | ≈ **3.2 s**（含 2 步+eval+装配） | 估算自 log |

### 5.2 预算（估算，标注 est）

| 方案 | Episodes | 请求 | 时间 est | Tokens est | 存储 est |
| --- | --- | --- | --- | --- | --- |
| 12×3×R2 | 72 | 144 | ≈ **4 min** | ≈ 144×290 ≈ **42k** | ≈ 15–30 MB |
| 12×3×R3 | 108 | 216 | ≈ **6 min** | ≈ **63k** | ≈ 25–45 MB |
| 24×3×R2 | 144 | 288 | ≈ **8 min** | ≈ **84k** | ≈ 40–70 MB |

GPU：本地 Q6_K，显存需求与 P1 相同（约 2–4GB 级，**以 P1 实测机器为准**——P1 未单列 VRAM 日志 → **VRAM = est/未测**）。

### 5.3 停止条件

| 条件 | 动作 |
| --- | --- |
| 安全违规（§4.1） | **立即停**，不继续臂 |
| 磁盘 < 2GB 或 server 拒绝连接 | 停 |
| 任务冻结失败 / 与 v1 泄漏 | 停，不跑 |
| 单 episode 失败率 > 50% 且非模型 NO_EDIT | 查 harness 再继续 |
| 预算超 2× 上表 token | 停，复盘 |

---

## 6. 大模型兼容性预审（不调用云端）

| 项 | 当前状态（本地 llama/OpenAI 兼容） | 租云前 | 最小改造 | 需真实请求？ |
| --- | --- | --- | --- | --- |
| 接口 | `chat_completion` OpenAI-compatible `/v1/chat/completions` | **P0** | base_url/api_key 可配置 | **P1 首次** |
| 上下文预算 | cfg context_window=8192 | **P0** | 按目标模型 max_context 覆盖 | 校准 P1 |
| Token 字段 | `usage.prompt_tokens/completion_tokens` | **P0** | 映射供应商字段 | **P1** |
| 供应商 token 口径 | chars/4 仅估算 | **P1** | 记录 provider 名与单位 | **P1** |
| cached_tokens | 服务端可选；禁作 KV 节省 | **P1** | 分列保存，不进门禁 | 披露 P1 |
| VP/ET/must 后端 | **模型无关**（harness 文本） | 不依赖云端 | 无 | 否 |
| 模型版本记录 | run_meta model 名 + 本地 sha | **P0** | 记录 api model id / 版本 | **P1** |
| 消息格式 | messages role/content 数组 | **P0** | 兼容 chat API；无强制 tools | **P1** |
| 错误/重试 | HTTP error → 记 error；无自动重试 | **P0** | 保留；供应商 429 需策略 | **P1** |
| 温度/seed | 0/0 写入 payload | **P0** | 某些云不支持 seed → 记录 | **P1** |

**P0（租用前必须）**：接口可配置、token 字段映射表、模型 id 记录、无硬编码本地路径依赖。  
**P1（首次校准）**：真实请求对齐 prompt/completion 计数、错误格式、max_context。  
**P2**：cached、seed 行为、供应商特有字段。  
**禁止**：为兼容性大规模重构 harness。

---

## 7. 最终决策（低成本单一路线）

| 问题 | 决定 |
| --- | --- |
| V13A 是否值得独立验证？ | **是**（M1 审计 PASS；无 V13A 实测；H1–H4 未验） |
| R=2 还是 R=3？ | **先 R=2**；方向模糊再 R=3 |
| 12 还是 24 新任务？ | **12 新任务**；不够则 8，禁止旧 24 冒充 |
| 本地模型是否足够？ | **是（当前阶段）**——1.5B 与 P1 同分布，足够做工程与探索 |
| 是否先改代码？ | **否**——M1 已可跑 V13A；仅当 holdout 任务格式与 runner 不兼容时再最小适配 |
| 租云前必须解决 | §6 **P0** 项：接口配置、token 映射、模型 id 记录 |
| 何结果应停止 V13A？ | ① 安全违规；② 新集上 ESR(V13A) < ESR(E)−0.10 且 TPAE ≥ TPAE(F)；③ 升级率≈100% 或 ≈0% 且无 hit/touch 区分 |

### 推荐路线（唯一）

1. **冻结 12 个新 holdout 任务**（类型配额固定，与 v1 文件 hash 不交）。  
2. 本地跑 **E / F / V13A × 12 × R=2**（72 eps / 144 请求），独立目录 + 随机 seed **20261103**。  
3. 报告 ESR/TPAE/TPSE/FETC + V13A 升级率 + 安全审计；标注探索性。  
4. 安全通过且 H1/H2 方向正确 → 再考虑 R=3 或云端大模型校准（P0 清单完成后再租）。  
5. 任一安全失败 → **停止 V13A 扩展**，回到 M1 修复审查。

---

## 8. 本阶段边界

- 未改代码/配置/冻结文档  
- 未跑模型/实验  
- 未申请云端  
- 未 Git 写操作  

**等待人工审阅本计划后，再决定是否创建 holdout 任务与开跑。**
