# V1.2-r2.2 P0 Smoke Post-Execution Review

性质：**只读**审查。输出：`p1/experiments/v12_p0_smoke/post_review/`。  
未改实验数据、代码、设计文档；未重跑模型。

---

## Overall Verdict

# CONDITIONAL PASS

| 维度 | 判定 |
| --- | --- |
| Data Integrity | **PASS** |
| Safety Audit | **PASS**（见安全口径说明） |
| Strategy Fidelity | **PASS** |
| Workspace Isolation | **CONDITIONAL**（结构隔离 OK；缺实验前全量 SHA 清单 → EVIDENCE GAP） |
| Git Integrity | **PASS** |
| P1 Review Recommendation | **RECOMMEND REVIEW**（≠ 授权 P1） |

---

## A. 数据完整性 — **PASS**

证据：`metric_recalculation.csv`、`metric_recalculation_integrity.json`、`per_step_all.csv`

| 检查 | 结果 |
| --- | --- |
| 32 Episode | 32/32，无 missing/extra |
| 每 Episode 2 steps | 全部 2 |
| 四臂各 8 | E/F/G/H=8 |
| 真实请求 | **64**（prompt_tokens>0；log 合计 64） |
| 遗漏/重复请求 | 未发现；order log 32 COMPLETED |
| summary 可从 per_step 重算 | **全部匹配**（ESR/SPR/TPAE/TPSE/FETC） |
| prompt_tokens | 全 >0 |
| NaN | 仅 `error` 空串被读成 NaN（64）→ **格式现象**，非缺失指标 |
| 零成功/零失败特殊值 | 本批各臂均有成功与失败，未触发 NA/∞；定义见 prereg |

**统计计算：无错误。**  
分类：无数据缺失、无口径不一致。

---

## B. 失败根因 — `failure_analysis.csv`

失败 step：**29**（episode 级失败更多，见 summary）。

| primary | 数量 | 说明 |
| --- | --- | --- |
| MODEL_NO_EDIT | 16 | 上下文含 FILE 仍 NO_EDIT（如 RUR02/DUP01 step1） |
| MODEL_REASONING_ERROR | 12 | 有 FILE 应用但 eval 失败（DUP01 step2 等） |
| UNDETERMINED | 1 | RFS01_F step1 写 mode 仅 docstring → 需人工看任务预期 |
| CONTEXT_MISSING / VP_ERROR / … | 0 | 本轮未出现 |

**未**把所有失败自动归为“模型边界”：已核对 context 是否含 FILE、psc_ok、applied、eval 原文。  
RUR02 类：**有 hot FULL 仍 NO_EDIT** → MODEL_NO_EDIT（信息在，模型未改）。  
证据路径列在 CSV `evidence_path`。

---

## C. 安全门禁 — **PASS**（分层陈述）

### C.1 本轮真实运行证据（64 步）

` safety_audit.csv`：

- `et_full_in_current_ctx`：**64/64 True**  
- `psc_ok`：**64 True**  
- `edit_target_full_verified`：**64 True**  
- INSUFFICIENT / error：**0**  
- 验证失败后仍请求：**0**（与 64 次成功 pre_send 一致）

### C.2 单元测试证据（非本轮）

- `test_v12_m3_fix01_gate.py`（10）：mock 断言失败时 **chat n=0**  
- 全量 181 passed（执行前）  

**不得混为一谈**：本轮 **INSUFFICIENT=0** 只说明未触发阻断；阻断逻辑在真实路径上 **未被正向触发验证**（NOT_VERIFIABLE for live-block-fire）。

### C.3 VP 语义边界

日志中的省略/可见性验证 = **VP（旧名 O′）**：仅证明满足可验证安全省略条件，**不**证明语义完全等价，**不**保证模型永不丢任务信息。

---

## D. 策略行为 — **PASS**

证据：`execution/runs/episodes/v1_RUR02/vam_coder_v1.2_*/steps/step1/context.txt`

| 臂 | 实际注入 | 符合预注册 |
| --- | --- | --- |
| E | hot **FILE** + stable **INDEX** | 是 |
| F | hot+stable **全 FILE** | 是 |
| G | 全 FILE | 是 |
| H | **仅 hot FILE** | 是 |

INDEX **未**被当作完整源码（无 FILE 围栏）。  
抽查：IRR01 E step2 alpha FILE + `a()`/`a2()` 保留。

---

## E. 工作区隔离 — **CONDITIONAL / EVIDENCE GAP**

| 检查 | 结果 |
| --- | --- |
| 32 独立 workspace 目录 | **PASS**（`runs/episodes/*/*/workspace` ×32） |
| 任务源目录仍为冻结两文件（IRR01） | **PASS**（alpha/beta） |
| 跨 Arm 共享可写盘 | **未发现**（每 episode 独立目录） |
| **实验开始前**全量 SHA 清单 | **EVIDENCE GAP**（阶段 B 有 snapshot_sha，但 execution 未落盘 per-episode 对账） |
| 执行后当前哈希 | 可生成，**不能**充当实验前证据 |

见 `evidence_gaps.md`。

---

## F. Git 与冻结 — **PASS**

`git_integrity_report.md`：

- branch `p1/v1.1`，HEAD `155f934…`  
- stash@{0} 未变  
- V1.0 三项 + 七份 r2.2 文档 SHA **OK**  
- 无 git 写操作  

---

## 研究结论（严格分层）

| RQ | 结论 |
| --- | --- |
| **RQ1** E 相对 F/G/H 初步效率信号 | **弱、探索性**：TPAE 各臂接近（539–556）；TPSE E/H 略低于 F，但 **n=8/臂**，**不能**称“E 更优”或统计显著。 |
| **RQ2** EditTarget FULL + VP 安全工程证据 | **有工程证据**：64 步 et_full/et_verified；IRR01 alpha 全文与 `a()` 保留；策略分层符合。 |
| **RQ3** 是否发现需修复实现问题 | **本轮未发现 BLOCKER 级实现错误**。次要：RFS01 单步 UNDETERMINED；缺实验前 workspace 哈希对账。 |
| **RQ4** 是否足以进入 P1 评审 | **RECOMMEND REVIEW**——工程链路与安全约束在 Smoke 中可追溯；**统计功效与架构有效性均未证明**。 |

**禁止表述**：不得写“显著优于”“证明架构有效”“非劣成立”。

---

## 分层结论一览

| 层级 | P0 是否支持 |
| --- | --- |
| 工程链路正确性 | **是**（32/32、64 请求、审计齐全） |
| 安全约束执行 | **是**（本轮路径）；阻断 **触发** 仅单测 |
| 模型任务能力 | 部分失败，主因 NO_EDIT/推理 |
| Token 效率 | 仅描述性；无臂间强结论 |
| 统计显著性 | **否** |
| 架构有效性 | **否（P0 不证明）** |

---

## P1 Review Recommendation

# RECOMMEND REVIEW

（进入 **P1 方案评审**，**不等于**授权执行 P1。）

---

## Outstanding Blockers / Risks

1. **EVIDENCE GAP**：无实验前 per-episode workspace 全量 SHA。  
2. **未在真实路径触发** INSUFFICIENT 阻断（仅单测）。  
3. 1 UNDETERMINED 失败（RFS01_F）。  
4. n 小，效率臂间差异不可推断。  
5. VP ≠ 语义等价（见总则）。

---

## 交付文件清单

- `post_smoke_review.md`（本文件）  
- `failure_analysis.csv`  
- `metric_recalculation.csv`  
- `safety_audit.csv`  
- `evidence_gaps.md`  
- `git_integrity_report.md`  
- 辅助：`_compute.py`、`metric_recalculation_integrity.json`  

等待你审阅；**不启动 P1**。
