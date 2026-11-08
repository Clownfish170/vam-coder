# V1.2-r2.2 P1 Pre-Execution Review

性质：**只读方案评审**。目录 `p1/experiments/v12_p1_review/`。  
未改代码/预注册/任务；未跑 P0/P1/模型。

---

## Overall

| 维度 | 判定 |
| --- | --- |
| **P1 Design Readiness** | **CONDITIONAL PASS** |
| Statistical Readiness | **CONDITIONAL**（预注册已自陈把握度不足） |
| Safety Readiness | **CONDITIONAL**（缺 live 阻断正样本；单测已覆盖） |
| Data Collection Readiness | **CONDITIONAL**（须补 step0/stepN workspace SHA） |
| Resource Readiness | **PASS**（可估算，见 resource_estimate） |
| **P1 Execution Recommendation** | **RECOMMEND EXECUTION REVIEW**（≠ 授权执行） |

---

## 1. 设计完整性（对照预注册 r2.2）

| 条款 | 状态 |
| --- | --- |
| §3 臂 A,B,D,E,F,G,H；P1=24×7×R3≈1008 请求 | 冻结完整 |
| §1.1 r2.2 行为（E/C FULL、分列 verified） | 与代码验收一致 |
| §5 指标 ESR/SPR/TPAE/TPSE/FETC | 与 P0 重算一致 |
| §6 门禁 ε/δ、TPSE≤0.95、TPAE≤1.05 | **未改**；须在 P1 前再冻结哈希 |
| §4 排除/重试/FETC 口径 | 明确 |
| RQ1 含 E vs D（v1.1） | 需 D 臂跑 v1.1 runner——工程上可行，见风险 |

**结论**：设计 **完整可评**；本轮 **不建议改** 臂/门禁/样本量（见 recommended_changes 仅操作层）。

---

## 2. 样本量与统计（B）

| 项 | 评估 |
| --- | --- |
| 每臂 72 episodes（24×R3） | 预注册已写 SE≈0.05–0.06；**对 5% TPSE / 10pp 非劣把握度有限** |
| R=3 | **探索性可接受**；不足以支撑强非劣声明 |
| task 聚类 bootstrap（seed 20261102） | **合理**（避免 rep 伪重复）；须保留全 R |
| 24 任务 | 覆盖机制面；**单模型**，外推受限 |
| 95% CI | 预期偏宽；报告须用“点估计门禁 + 宽 CI”句式（prereg §4） |
| 5% TPSE | 在臂间 TPAE 仅差 ~1–3% 的 P0 形态下，**难检出**；勿事后改 δ |

**Statistical Readiness：CONDITIONAL** — 仅支持探索性与门禁点估计，不支持“已证非劣”。

---

## 3. P0 失败对 P1 解释的影响（A）

P0：NO_EDIT 16 · REASONING 12 · UNDETERMINED 1。

| 影响 | 判断 |
| --- | --- |
| 降低统计功效 | **是** — 任务级失败集中在 RUR02/DUP01/RUR03（模型侧），压低 ESR 并增大方差 |
| ESR 解释 | 臂间差异可能被 **模型瓶颈** 主导，而非注入策略；须分层报告失败类别 |
| Token 效率偏差 | 失败 episode 仍产生 token → TPSE/TPAE 含失败成本；符合预注册，**不可**删失败任务 |
| 模型能力瓶颈 | **是** — 不得删除困难任务或改成功标准；报告须标 MODEL_* 占比 |

**禁止**：为提高 ESR 剔除 RUR* / DUP01。

---

## 4. 安全门禁（C）

| 门禁 | 单测 | 集成/dry-run | P0 真实 |
| --- | --- | --- | --- |
| verify 失败 → 0 请求 | **有**（10） | — | **未触发**（0 INSUFFICIENT） |
| 缺 must → INSUFFICIENT | 有 | 有 | 未触发 |
| E/C 禁 VP 省略 | 有 | 有 | et_verified 64/64 |
| pre_send ≡ 最终消息 | 代码路径 | dry-run | P0 psc_ok 64/64 |

**Safety Readiness：CONDITIONAL** —  
P1 前建议：**不改算法** 的前提下，可选加 **只读审计脚本** 对每步 `messages_sha` vs `pre_send_check` 抽样；或接受单测+P0 作为门禁证据。  
**INSUFFICIENT live 触发** 仍为 NOT_VERIFIABLE（除非故障注入，且不得进正式指标）。

---

## 5. Workspace（D）— P1 必须补强

P0 后审 EVIDENCE GAP：缺实验前逐文件 SHA。

**P1 采集规范（建议写入执行手册，不改预注册数字）**：

```text
episode start:
  copy frozen project → workspaces/<episode_id>/
  write workspace_manifest_pre.json   # file → sha256, dir_hash
episode end:
  write workspace_manifest_post.json
  write workspace_diff.json           # added / modified / deleted
  freeze; never write to p1/tasks/**
```

每 Arm 独立目录；禁止共享可写 workspace。  
**Data Collection Readiness：CONDITIONAL**，补上后可 PASS。

---

## 6. 指标与统计口径（E）

| 指标 | 预注册 | P0 重算 | P1 注意 |
| --- | --- | --- | --- |
| ESR/SPR/TPAE/TPSE/FETC | §5 | 一致 | 主表四列 |
| 95% CI | Wilson + Bootstrap | — | 宽 CI 必报 |
| 零成功 TPSE | NA/∞ | 未触发 | 按 prereg |
| 零失败 FETC_mean | NA | 未触发 | 按 prereg |
| cached_tokens | 禁止当 KV 节省 | 未滥用 | 分列 prefill |
| 多臂比较 | RQ 映射 | — | 禁止“显著优于”措辞 |

---

## 7. 可追溯性（G/H）

| 项 | P0 | P1 要求 |
| --- | --- | --- |
| pre_send / injection_audit / messages | 有 | 保留 |
| execution_order 随机化 | seed 20261102 | P1 **新**随机清单（可另 seed，须预注册记录） |
| 失败归因 CSV | 有 | 扩展 24 任务 |
| git/stash | PASS | 每阶段再核 |

---

## 8. 资源与时间

见 `resource_estimate.md`：约 **1008** 请求 + A/B/D 臂；建议串行 pause≥1s → **数小时级**（约 1.5–4h，视 eval）。

---

## 9. P1 执行风险

见 `risk_register.csv`（Top：模型瓶颈功效、D 臂双 runner、workspace 审计缺口、时长）。

---

## 10. 结论

| 项 | 结果 |
| --- | --- |
| P1 Design Readiness | **CONDITIONAL PASS** |
| Statistical Readiness | **CONDITIONAL** |
| Safety Readiness | **CONDITIONAL** |
| Data Collection Readiness | **CONDITIONAL** |
| Resource Readiness | **PASS** |
| **P1 Execution Recommendation** | **RECOMMEND EXECUTION REVIEW** |

**RECOMMEND EXECUTION REVIEW ≠ 授权执行 P1。**  
等待你审阅 `recommended_changes.md` 与本报告后再决定。
