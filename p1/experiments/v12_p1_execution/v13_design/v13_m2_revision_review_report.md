# V1.3 M2-Revision Review 报告

审查性质：**只读**。未改代码/计划/任务；未跑模型；无 Git 写。  
审查对象：

| 文件 | 状态 |
| --- | --- |
| `v13_m2_validation_plan_rev2.md` | 存在，已读 |
| `v13_m2_revision_response.md` | 存在，已读 |
| `v13_m2_validation_plan.md`（原） | 存在，已读 |
| `v13_m2_review_report.md` | 存在，已读 |
| V1.2 prereg / method | 存在（只读交叉） |
| SYSTEM_PROMPT 实测哈希 | `4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a` = rev2 所写值 |

Git：分支 `p1/v1.1` · HEAD `155f934bc6c565bd304b2b7438259d592bc348c8` · stash@{0} 未动。

---

## 1. P1-01 至 P1-10 逐项

### P1-01 停止条件 S1–S7 — **PARTIAL**

| 项 | 结论 |
| --- | --- |
| S1–S6 并入原 §5.3/§7 | **PASS**：安全/磁盘/泄漏/失败率/预算/ESR+TPAE 条件齐全，与原 §7 数值一致 |
| S7「分布不可区分」 | **FAIL（可执行性）** |
| hit/touch 统计单位 | **未定义**（按文件？按升级事件？按 episode？） |
| 「unexplained」判定 | **未定义**（无客观规则） |
| 比较对象/指标/统计方法 | **未定义**（Full 比率差？何种距离？是否 CI？） |

**结论：PARTIAL。** S1–S6 可执行；**S7 仅文字，不可计算**，不得视为已关闭。  
**未改**原阈值数值（合格）。

### P1-02 统计方法 — **FAIL（冻结冲突）**

| 项 | 结论 |
| --- | --- |
| task_id 聚类 | **PASS**（§4.3） |
| B=10000 | **PASS**（与 P1/prereg 一致） |
| seed | **冲突** |
| 版本变更记录 | **无** |

- 冻结 prereg：bootstrap seed = **20261102**  
- rev2：bootstrap seed = **20261103**（且写“方法与 P1 相同”）  
- **未**提供正式变更记录，**不能**视为兼容。

**结论：FAIL（相对“进入 Holdout 前关闭”）。**  
必须：改回 **20261102**，或补充经批准的 seed 变更记录后再审。

### P1-03 Prompt 冻结 — **PARTIAL**

| 项 | 结论 |
| --- | --- |
| SYSTEM_PROMPT SHA256 | **PASS**（与 `p1_common.SYSTEM_PROMPT` 实测一致） |
| build_messages 代码版本/哈希 | **FAIL（缺）**：仅文字模板，**无**函数文件 sha |
| 消息顺序/角色/history=keep/注入位置 | **PARTIAL**：“沿用 runner 现行逻辑”未钉死 history 构造步骤 |

**结论：PARTIAL。** 系统提示词可复现；**用户消息与历史构造未完全冻结**。

### P1-04 逐步字段 — **PARTIAL**

| 项 | 结论 |
| --- | --- |
| 覆盖 episode×step 文件清单 | **PASS** |
| result 关键字段 | **PASS**（可重建 ESR/SPR/TPAE/TPSE/FETC/Prefill/INSUFFICIENT） |
| 每字段类型/来源/时点/缺失规则 | **FAIL（不完整）** |
| DHO 等安全指标日志源 | **PARTIAL**（写“见 method”但未映射到具体文件字段名） |

**结论：PARTIAL。** 主指标可重建；审计字段规范不足。

### P1-05 三臂隔离 — **PASS**

§2.3 单一冻结源 copy、禁跨臂复制、step2 仅本臂。  
（快照哈希：§2.2 holdout_manifest 含 project_files_sha256 → **PASS**。）

### P1-06 Prefill — **PASS**

§3.4.1：主指标 = `prompt_tokens`；cached 分列；禁止 KV 节省表述。

### P1-07 NA 规则 — **PASS**

§3.4.2：零成功 TPSE=NA/∞；零失败 FETC_mean=NA；回指 method §1.3；禁止当 0。

### P1-08 NOT_TRIGGERED — **PASS**

§4.4：不得计为 PASS。  
（完整枚举 PASS/FAIL/NA/N/A/INSUFFICIENT 字典可再加强 → **P2**，不阻断。）

### P1-09 错误分类 — **PARTIAL**

§4.4：协议错误≠架构。  
**缺**：task failure / infrastructure failure 分类，以及各类是否计入 ESR、失败率、S4 的**完整**矩阵。

### P1-10 失败率 — **PARTIAL**

| 项 | 结论 |
| --- | --- |
| 分子/分母 | **PASS**：失败 episode / 尝试 episode |
| 多 step 重复计数 | **PASS**（episode 级） |
| 统计窗口 | **PARTIAL**：未写“全 run 还是滚动窗” |
| 新增百分比阈值 | **PASS**（未新增；保留原 &gt;50% 观察） |

---

## 2. 全局一致性

| 检查 | 结果 |
| --- | --- |
| V13A 算法 | **未改** |
| 臂 E/F/V13A | **未改** |
| 12 全新 holdout、禁旧 24 | **未改** |
| R=2 探索 | **未改** |
| 72 eps / 144 req | **未改** |
| ET/C/must/O′/INSUFFICIENT | **未改** |
| ESR/TPAE/TPSE 阈值 0.05 等 | **未改** |
| 新模型调用/自动重试/反馈环 | **无** |
| 原计划未被覆盖 | **PASS** |
| 原计划 vs rev2 vs response | 主体一致；**P1-02 seed** 与冻结 prereg **不一致** |

---

## 3. 哈希与冻结

| 项 | 结果 |
| --- | --- |
| HEAD / stash | 符合预期，未动 |
| SYSTEM_PROMPT sha | **与代码一致** |
| prereg bootstrap seed 20261102 | **仍在冻结文档**；rev2 用 20261103 → **冲突未记录** |
| 代码/任务/原计划 | 本审查未改 |

---

## 4. 未解决问题与风险

| 级别 | ID | 问题 |
| --- | --- | --- |
| **阻断 Holdout** | R1 | bootstrap seed 与冻结 prereg 冲突且无变更记录 |
| **阻断 Holdout** | R2 | S7 不可执行（无比较指标/方法/单位） |
| 应补 | R3 | build_messages 哈希/history 构造未钉死 |
| 应补 | R4 | per-step 字段类型/缺失规则、DHO 字段映射 |
| 应补 | R5 | 错误四分类与 ESR/S4 计入规则 |
| 非阻断 | R6 | S4 窗口表述、NOT_TRIGGERED 枚举字典 |

---

## 5. 最终结论

# CONDITIONAL PASS

**含义**：无安全 P0；rev2 大幅关闭 P1，但 **R1（seed 冻结冲突）与 R2（S7 不可执行）必须先解决** 才能进入 **M2-Holdout Freeze**。

### 进入 Holdout Freeze 前必须

1. **bootstrap seed**：恢复 **20261102**（与 prereg 一致）**或** 出具正式变更记录并更新冻结说明；  
2. **S7**：补比较对象、指标（如 related Full 比例）、判定规则与 hit/touch 单位，或降级为纯诊断不进入停机表；  
3. （建议一并）R3–R5 文案。

**本审查未修改任何文件。** 等待你决定是否按上述条件改 rev2 后再审，或接受条件清单进入下一阶段流程。
